import logging
import pkgutil
import sys
import unittest

import segment.analytics as analytics
from segment.analytics.client import Client


def all_names():
    for _, modname, _ in pkgutil.iter_modules(__path__):
        yield 'segment.analytics.test.' + modname


def all():
    logging.basicConfig(stream=sys.stderr)
    return unittest.defaultTestLoader.loadTestsFromNames(all_names())


class TestInit(unittest.TestCase):
    def test_writeKey(self):
        self.assertIsNone(analytics.default_client)
        analytics.flush()
        self.assertEqual(analytics.default_client.write_key, 'test-init')

    def test_debug(self):
        self.assertIsNone(analytics.default_client)
        analytics.debug = True
        analytics.flush()
        self.assertTrue(analytics.default_client.debug)
        analytics.default_client = None
        analytics.debug = False
        analytics.flush()
        self.assertFalse(analytics.default_client.debug)
        analytics.default_client.log.setLevel(0)  # reset log level after debug enable

    def test_gzip(self):
        self.assertIsNone(analytics.default_client)
        analytics.gzip = True
        analytics.flush()
        self.assertTrue(analytics.default_client.gzip)
        analytics.default_client = None
        analytics.gzip = False
        analytics.flush()
        self.assertFalse(analytics.default_client.gzip)

    def test_host(self):
        self.assertIsNone(analytics.default_client)
        analytics.host = 'http://test-host'
        analytics.flush()
        self.assertEqual(analytics.default_client.host, 'http://test-host')
        analytics.host = None
        analytics.default_client = None

    def test_max_queue_size(self):
        self.assertIsNone(analytics.default_client)
        analytics.max_queue_size = 1337
        analytics.flush()
        self.assertEqual(analytics.default_client.queue.maxsize, 1337)

    def test_max_retries(self):
        self.assertIsNone(analytics.default_client)
        client = Client('testsecret', max_retries=42)
        for consumer in client.consumers:
            self.assertEqual(consumer.retries, 42)

    def test_sync_mode(self):
        self.assertIsNone(analytics.default_client)
        analytics.sync_mode = True
        analytics.flush()
        self.assertTrue(analytics.default_client.sync_mode)
        analytics.default_client = None
        analytics.sync_mode = False
        analytics.flush()
        self.assertFalse(analytics.default_client.sync_mode)

    def test_timeout(self):
        self.assertIsNone(analytics.default_client)
        analytics.timeout = 1.234
        analytics.flush()
        self.assertEqual(analytics.default_client.timeout, 1.234)

    def setUp(self):
        analytics.write_key = 'test-init'
        analytics.default_client = None


if __name__ == '__main__':
    unittest.main()
