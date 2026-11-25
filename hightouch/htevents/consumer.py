import json
import logging
import time
from collections import deque
from queue import Empty, Full
from threading import Condition, Thread

import backoff
from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError,
    ContentDecodingError,
    Timeout,
)

from hightouch.htevents.request import APIError, DatetimeSerializer, post

MAX_MSG_SIZE = 32 << 10

# Our servers only accept batches less than 500KB. Here limit is set slightly
# lower to leave space for extra data that will be added later, eg. "sentAt".
BATCH_SIZE_LIMIT = 475000


class FatalError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        msg = '[Hightouch] {0})'
        return msg.format(self.message)


class SourceRecovery:
    """Coordinate delivery turns and backoff across consumers of the same source."""

    def __init__(self):
        self.condition = Condition()
        self.pending = deque()
        self.probing = False
        self.deadline = 0
        self.delay = 1
        self.closing = False
        self.closed_during_recovery = False
        self.prefer_fresh = False

    def enqueue(self, queue, item):
        with self.condition:
            if (
                (self.pending or self.probing)
                and queue.maxsize > 0
                and queue.unfinished_tasks >= queue.maxsize
            ):
                raise Full
            queue.put_nowait(item)

    def defer(self, batch, error, probe):
        with self.condition:
            if self.closing:
                return False
            self.pending.append((batch, error))
            if probe:
                self.probing = False
            if probe or not self.deadline:
                self.deadline = time.monotonic() + self.delay
                self.delay = min(60, self.delay * 2)
            self.condition.notify_all()
            return True

    def next_probe(self, next_fresh):
        with self.condition:
            while self.probing or self.pending:
                remaining = None if self.probing else self.deadline - time.monotonic()
                if remaining is None or remaining > 0:
                    self.condition.wait(remaining)
                    continue
                if self.prefer_fresh:
                    batch = next_fresh(block=False)
                    if batch:
                        self.probing = True
                        self.prefer_fresh = False
                        return batch
                self.probing = True
                self.prefer_fresh = True
                batch, _ = self.pending.popleft()
                return batch
            return None

    def hold_if_paused(self, batch):
        with self.condition:
            if self.closed_during_recovery:
                raise FatalError('Client closed during source recovery')
            if self.closing or not (self.pending or self.probing):
                return False
            self.pending.append(
                (batch, RuntimeError('Client closed during source recovery'))
            )
            return True

    def finish_probe(self):
        with self.condition:
            self.probing = False
            self.deadline = 0
            self.delay = 1
            self.condition.notify_all()

    def close(self):
        with self.condition:
            if not self.closing:
                self.closed_during_recovery = bool(self.pending or self.probing)
            self.closing = True
            pending, self.pending = self.pending, deque()
            self.condition.notify_all()
            return pending


class Consumer(Thread):
    """Consumes the messages from the client's queue."""

    log = logging.getLogger('hightouch')

    def __init__(
        self,
        queue,
        write_key,
        upload_size=100,
        host=None,
        on_error=None,
        upload_interval=0.5,
        gzip=False,
        retries=10,
        timeout=15,
        proxies=None,
        oauth_manager=None,
        recovery=None,
    ):
        """Create a consumer thread."""
        Thread.__init__(self)
        # Make consumer a daemon thread so that it doesn't block program exit
        self.daemon = True
        self.upload_size = upload_size
        self.upload_interval = upload_interval
        self.write_key = write_key
        self.host = host
        self.on_error = on_error
        self.queue = queue
        self.gzip = gzip
        # It's important to set running in the constructor: if we are asked to
        # pause immediately after construction, we might set running to True in
        # run() *after* we set it to False in pause... and keep running
        # forever.
        self.running = True
        self.recovery = recovery or SourceRecovery()
        self.retries = retries
        self.timeout = timeout
        self.proxies = proxies
        self.oauth_manager = oauth_manager

    def run(self):
        """Runs the consumer."""
        self.log.debug('consumer is running...')
        while self.running:
            self.upload()

        self.log.debug('consumer exited.')

    def pause(self):
        """Pause the consumer."""
        self.running = False
        self.stop_recovery()

    def stop_recovery(self):
        for batch, error in self.recovery.close():
            self.finish(batch, error)

    def finish(self, batch, error=None):
        if error:
            self.log.error('error uploading: %s', error)
            if self.on_error:
                try:
                    self.on_error(error, batch)
                except Exception:
                    # A raising callback must not kill the consumer thread.
                    self.log.exception('error in on_error callback')
        for _ in batch:
            self.queue.task_done()

    def upload(self):
        """Upload the next batch of items, return whether successful."""
        batch = self.recovery.next_probe(self.next)
        probe = batch is not None
        if not probe:
            if not self.running:
                return False
            batch = self.next()
            if not batch:
                return False
        try:
            if probe:
                self.post(batch)
            elif self.request(batch) is False:
                return False
        except Exception as error:
            transient = isinstance(
                error,
                (ConnectionError, Timeout, ChunkedEncodingError, ContentDecodingError),
            ) or (
                isinstance(error, APIError)
                and (error.status in (408, 429) or 500 <= error.status < 600)
            )
            if transient and self.recovery.defer(batch, error, probe):
                self.log.warning('Deferring batch after collector failure: %s', error)
                return False
            self.finish(batch, error)
            success = False
        else:
            self.finish(batch)
            success = True
        if probe:
            self.recovery.finish_probe()
        return success

    def next(self, block=True):
        """Return the next batch of items to upload."""
        queue = self.queue
        items = []

        start_time = time.monotonic()
        total_size = 0

        while len(items) < self.upload_size:
            elapsed = time.monotonic() - start_time
            if elapsed >= self.upload_interval:
                break
            try:
                item = queue.get(block=block, timeout=self.upload_interval - elapsed)
                item_size = len(json.dumps(item, cls=DatetimeSerializer).encode())
                if item_size > MAX_MSG_SIZE:
                    self.log.error('Item exceeds 32kb limit, dropping. (%s)', str(item))
                    continue
                items.append(item)
                total_size += item_size
                if total_size >= BATCH_SIZE_LIMIT:
                    self.log.debug('hit batch size limit (size: %d)', total_size)
                    break
            except Empty:
                break
            except Exception as e:
                self.log.exception('Exception: %s', e)

        return items

    def request(self, batch):
        """Attempt to upload the batch and retry before raising an error"""

        def fatal_exception(exc):
            if isinstance(exc, APIError):
                return 400 <= exc.status < 500 and exc.status not in (408, 429)
            elif isinstance(exc, FatalError):
                return True
            else:
                # retry on all other errors (eg. network)
                return False

        @backoff.on_exception(
            backoff.expo, Exception, max_tries=self.retries + 1, giveup=fatal_exception
        )
        def send_request():
            if self.recovery.hold_if_paused(batch):
                return False
            self.post(batch)
            return True

        return send_request()

    def post(self, batch):
        post(
            self.write_key,
            self.host,
            gzip=self.gzip,
            timeout=self.timeout,
            batch=batch,
            proxies=self.proxies,
            oauth_manager=self.oauth_manager,
        )
