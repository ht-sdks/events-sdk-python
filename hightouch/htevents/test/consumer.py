import json
import time
import unittest

import mock

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from hightouch.htevents.consumer import MAX_MSG_SIZE, Consumer
from hightouch.htevents.request import APIError

from .constants import TEST_WRITE_KEY


class TestConsumer(unittest.TestCase):
    def test_next(self):
        q = Queue()
        consumer = Consumer(q, '')
        q.put(1)
        next = consumer.next()
        self.assertEqual(next, [1])

    def test_next_limit(self):
        q = Queue()
        upload_size = 50
        consumer = Consumer(q, '', upload_size)
        for i in range(10000):
            q.put(i)
        next = consumer.next()
        self.assertEqual(next, list(range(upload_size)))

    def test_dropping_oversize_msg(self):
        q = Queue()
        consumer = Consumer(q, '')
        oversize_msg = {'m': 'x' * MAX_MSG_SIZE}
        q.put(oversize_msg)
        next = consumer.next()
        self.assertEqual(next, [])
        self.assertTrue(q.empty())

    def test_upload(self):
        q = Queue()
        consumer = Consumer(q, TEST_WRITE_KEY)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        q.put(track)
        success = consumer.upload()
        self.assertTrue(success)

    def test_upload_failure_returns_false_and_acks_queue(self):
        q = Queue()
        consumer = Consumer(q, TEST_WRITE_KEY)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        q.put(track)
        with mock.patch.object(
            consumer, 'request', side_effect=Exception('upload failed')
        ):
            success = consumer.upload()
        self.assertFalse(success)
        self.assertTrue(q.empty())
        q.join()

    def test_on_error_called_on_upload_failure(self):
        q = Queue()
        errors = []

        def on_error(error, batch):
            errors.append((error, batch))

        consumer = Consumer(q, TEST_WRITE_KEY, on_error=on_error)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        q.put(track)
        upload_error = Exception('upload failed')
        with mock.patch.object(consumer, 'request', side_effect=upload_error):
            success = consumer.upload()
        self.assertFalse(success)
        self.assertEqual(len(errors), 1)
        self.assertIs(errors[0][0], upload_error)
        self.assertEqual(errors[0][1], [track])
        q.join()

    def test_on_error_exception_does_not_propagate(self):
        q = Queue()

        def on_error(error, batch):
            raise RuntimeError('callback failed')

        consumer = Consumer(q, TEST_WRITE_KEY, on_error=on_error)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        q.put(track)
        with mock.patch.object(
            consumer, 'request', side_effect=Exception('upload failed')
        ):
            # Capture logs so the intentional traceback is not emitted to
            # stderr (GitHub Actions would annotate it as a check failure).
            with self.assertLogs('hightouch', level='ERROR') as logs:
                success = consumer.upload()
        self.assertFalse(success)
        self.assertTrue(q.empty())
        q.join()
        self.assertTrue(
            any('error in on_error callback' in message for message in logs.output)
        )

    def test_on_error_exception_does_not_stop_consumer(self):
        q = Queue()

        def on_error(error, batch):
            raise RuntimeError('callback failed')

        consumer = Consumer(
            q, TEST_WRITE_KEY, on_error=on_error, retries=0, upload_interval=0.1
        )
        with mock.patch(
            'hightouch.htevents.consumer.post', side_effect=Exception('upload failed')
        ):
            with self.assertLogs('hightouch', level='ERROR'):
                consumer.start()
                q.put({'type': 'track', 'event': 'e1', 'userId': 'userId'})
                q.join()
                q.put({'type': 'track', 'event': 'e2', 'userId': 'userId'})
                q.join()
                self.assertTrue(consumer.is_alive())
                consumer.pause()
                consumer.join(timeout=2)

    def test_upload_interval(self):
        # Put _n_ items in the queue, pausing a little bit more than
        # _upload_interval_ after each one.
        # The consumer should upload _n_ times.
        q = Queue()
        upload_interval = 0.3
        consumer = Consumer(
            q, TEST_WRITE_KEY, upload_size=10, upload_interval=upload_interval
        )
        with mock.patch('hightouch.htevents.consumer.post') as mock_post:
            consumer.start()
            for i in range(0, 3):
                track = {
                    'type': 'track',
                    'event': 'python event %d' % i,
                    'userId': 'userId',
                }
                q.put(track)
                time.sleep(upload_interval * 1.1)
            self.assertEqual(mock_post.call_count, 3)

    def test_multiple_uploads_per_interval(self):
        # Put _upload_size*2_ items in the queue at once, then pause for
        # _upload_interval_. The consumer should upload 2 times.
        q = Queue()
        upload_interval = 0.5
        upload_size = 10
        consumer = Consumer(
            q, TEST_WRITE_KEY, upload_size=upload_size, upload_interval=upload_interval
        )
        with mock.patch('hightouch.htevents.consumer.post') as mock_post:
            consumer.start()
            for i in range(0, upload_size * 2):
                track = {
                    'type': 'track',
                    'event': 'python event %d' % i,
                    'userId': 'userId',
                }
                q.put(track)
            time.sleep(upload_interval * 1.1)
            self.assertEqual(mock_post.call_count, 2)

    @classmethod
    def test_request(cls):
        consumer = Consumer(None, TEST_WRITE_KEY)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        consumer.request([track])

    def _test_request_retry(self, consumer, expected_exception, exception_count):
        def mock_post(*args, **kwargs):
            mock_post.call_count += 1
            if mock_post.call_count <= exception_count:
                raise expected_exception

        mock_post.call_count = 0

        with mock.patch(
            'hightouch.htevents.consumer.post', mock.Mock(side_effect=mock_post)
        ):
            track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
            # request() should succeed if the number of exceptions raised is
            # less than the retries parameter.
            if exception_count <= consumer.retries:
                consumer.request([track])
            else:
                # if exceptions are raised more times than the retries
                # parameter, we expect the exception to be returned to
                # the caller.
                try:
                    consumer.request([track])
                except type(expected_exception) as exc:
                    self.assertEqual(exc, expected_exception)
                else:
                    self.fail(
                        'request() should raise an exception if still failing '
                        'after %d retries' % consumer.retries
                    )

    def test_request_retry(self):
        # we should retry on general errors
        consumer = Consumer(None, TEST_WRITE_KEY)
        self._test_request_retry(consumer, Exception('generic exception'), 2)

        # we should retry on server errors
        consumer = Consumer(None, TEST_WRITE_KEY)
        self._test_request_retry(
            consumer, APIError(500, 'code', 'Internal Server Error'), 2
        )

        # we should retry on HTTP 429 errors
        consumer = Consumer(None, TEST_WRITE_KEY)
        self._test_request_retry(
            consumer, APIError(429, 'code', 'Too Many Requests'), 2
        )

        # we should NOT retry on other client errors
        consumer = Consumer(None, TEST_WRITE_KEY)
        api_error = APIError(400, 'code', 'Client Errors')
        try:
            self._test_request_retry(consumer, api_error, 1)
        except APIError:
            pass
        else:
            self.fail('request() should not retry on client errors')

        # test for number of exceptions raise > retries value
        consumer = Consumer(None, TEST_WRITE_KEY, retries=3)
        self._test_request_retry(
            consumer, APIError(500, 'code', 'Internal Server Error'), 3
        )

    def test_pause(self):
        consumer = Consumer(None, TEST_WRITE_KEY)
        consumer.pause()
        self.assertFalse(consumer.running)

    def test_max_batch_size(self):
        q = Queue()
        consumer = Consumer(q, TEST_WRITE_KEY, upload_size=100000, upload_interval=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        msg_size = len(json.dumps(track).encode())
        # number of messages in a maximum-size batch
        n_msgs = int(475000 / msg_size)

        def mock_post_fn(_, data, **kwargs):
            res = mock.Mock()
            res.status_code = 200
            self.assertTrue(
                len(data.encode()) < 500000,
                'batch size (%d) exceeds 500KB limit' % len(data.encode()),
            )
            return res

        with mock.patch(
            'hightouch.htevents.request._session.post', side_effect=mock_post_fn
        ) as mock_post:
            consumer.start()
            for _ in range(0, n_msgs + 2):
                q.put(track)
            q.join()
            self.assertEqual(mock_post.call_count, 2)

    @classmethod
    def test_proxies(cls):
        consumer = Consumer(None, TEST_WRITE_KEY, proxies='203.243.63.16:80')
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        consumer.request([track])
