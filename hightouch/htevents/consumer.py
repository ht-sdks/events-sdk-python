import json
import logging
import time
from collections import deque
from queue import Empty, Full, Queue
from threading import Thread

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


class DeliveryQueue(Queue):
    """Fresh events and deferred batches share the configured waiting capacity."""

    def __init__(self, maxsize):
        super().__init__(maxsize)
        self.deferred = deque()
        self.deferred_size = 0
        self.reserved_size = 0  # Includes deferred batches currently being uploaded.
        self.closing = False

    def _put(self, item):
        if self.maxsize > 0 and len(self.queue) + self.reserved_size >= self.maxsize:
            raise Full
        super()._put(item)

    def defer(self, batch, error, delay, reserved):
        with self.mutex:
            new_slots = 0 if reserved else len(batch)
            size = len(self.queue) + self.reserved_size + new_slots
            if self.closing or (self.maxsize > 0 and size > self.maxsize):
                return False
            self.deferred.append((time.monotonic() + delay, batch, error))
            self.reserved_size += new_slots
            self.deferred_size += len(batch)
            self.all_tasks_done.notify_all()
            return True

    def take_deferred(self, prefer_fresh):
        with self.mutex:
            if prefer_fresh and self.queue:
                return None
            if self.deferred and self.deferred[0][0] <= time.monotonic():
                _, batch, _ = self.deferred.popleft()
                self.deferred_size -= len(batch)
                return batch
            return None

    def release(self, batch):
        with self.mutex:
            self.reserved_size -= len(batch)

    def join_eligible(self):
        with self.all_tasks_done:
            self.all_tasks_done.wait_for(
                lambda: self.unfinished_tasks == self.deferred_size
                and (not self.deferred or self.deferred[0][0] > time.monotonic())
            )

    def task_done(self):
        super().task_done()
        with self.all_tasks_done:
            if self.unfinished_tasks == self.deferred_size:
                self.all_tasks_done.notify_all()

    def close_recovery(self):
        with self.mutex:
            self.closing = True
            pending, self.deferred = self.deferred, deque()
            self.reserved_size -= self.deferred_size
            self.deferred_size = 0
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
        self.prefer_fresh = False
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

    def upload(self):
        """Upload the next batch of items, return whether successful."""
        recovery = self.queue if isinstance(self.queue, DeliveryQueue) else None
        batch = (
            recovery.take_deferred(self.prefer_fresh) if recovery is not None else None
        )
        probe = self.prefer_fresh = batch is not None
        if batch is None:
            batch = self.next()
        if not batch:
            return False

        try:
            if probe:
                self.post(batch)
            else:
                self.request(batch)
        except Exception as error:
            transient = isinstance(
                error,
                (ConnectionError, Timeout, ChunkedEncodingError, ContentDecodingError),
            ) or (
                isinstance(error, APIError)
                and (error.status in (408, 429) or 500 <= error.status < 600)
            )
            if (
                transient
                and recovery is not None
                and recovery.defer(batch, error, self.upload_interval, reserved=probe)
            ):
                return False
            if probe:
                recovery.release(batch)
            self.finish(batch, error)
            return False
        if probe:
            recovery.release(batch)
        self.finish(batch)
        return True

    def finish(self, batch, error=None):
        if error is not None:
            self.log.error('error uploading: %s', error)
            if self.on_error:
                try:
                    self.on_error(error, batch)
                except Exception:
                    self.log.exception('error in on_error callback')
        for _ in batch:
            self.queue.task_done()

    def next(self):
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
                item = queue.get(block=True, timeout=self.upload_interval - elapsed)
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
            self.post(batch)

        send_request()

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
