import logging
import pkgutil
import sys
import unittest

import hightouch.htevents as htevents
from hightouch.htevents.client import Client

from .constants import TEST_WRITE_KEY


def all_names():
    for _, modname, _ in pkgutil.iter_modules(__path__):
        yield 'hightouch.htevents.test.' + modname


def all():
    logging.basicConfig(stream=sys.stderr)
    return unittest.defaultTestLoader.loadTestsFromNames(all_names())


class TestInit(unittest.TestCase):
    def test_writeKey(self):
        self.assertIsNone(htevents.default_client)
        htevents.flush()
        self.assertEqual(htevents.default_client.write_key, 'test-init')

    def test_debug(self):
        self.assertIsNone(htevents.default_client)
        htevents.debug = True
        htevents.flush()
        self.assertTrue(htevents.default_client.debug)
        htevents.default_client = None
        htevents.debug = False
        htevents.flush()
        self.assertFalse(htevents.default_client.debug)
        htevents.default_client.log.setLevel(0)  # reset log level after debug enable

    def test_gzip(self):
        self.assertIsNone(htevents.default_client)
        htevents.gzip = True
        htevents.flush()
        self.assertTrue(htevents.default_client.gzip)
        htevents.default_client = None
        htevents.gzip = False
        htevents.flush()
        self.assertFalse(htevents.default_client.gzip)

    def test_host(self):
        self.assertIsNone(htevents.default_client)
        htevents.host = 'http://test-host'
        htevents.flush()
        self.assertEqual(htevents.default_client.host, 'http://test-host')
        htevents.host = None
        htevents.default_client = None

    def test_max_queue_size(self):
        self.assertIsNone(htevents.default_client)
        htevents.max_queue_size = 1337
        htevents.flush()
        self.assertEqual(htevents.default_client.queue.maxsize, 1337)

    def test_max_retries(self):
        self.assertIsNone(htevents.default_client)
        client = Client(TEST_WRITE_KEY, max_retries=42)
        for consumer in client.consumers:
            self.assertEqual(consumer.retries, 42)

    def test_sync_mode(self):
        self.assertIsNone(htevents.default_client)
        htevents.sync_mode = True
        htevents.flush()
        self.assertTrue(htevents.default_client.sync_mode)
        htevents.default_client = None
        htevents.sync_mode = False
        htevents.flush()
        self.assertFalse(htevents.default_client.sync_mode)

    def test_timeout(self):
        self.assertIsNone(htevents.default_client)
        htevents.timeout = 1.234
        htevents.flush()
        self.assertEqual(htevents.default_client.timeout, 1.234)

    def setUp(self):
        htevents.write_key = 'test-init'
        htevents.default_client = None


if __name__ == '__main__':
    unittest.main()
