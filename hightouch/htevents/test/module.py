import unittest

import hightouch.htevents as htevents

from .constants import TEST_WRITE_KEY


class TestModule(unittest.TestCase):
    # def failed(self):
    #     self.failed = True

    def setUp(self):
        self.failed = False
        htevents.write_key = TEST_WRITE_KEY
        htevents.on_error = self.failed

    def test_no_write_key(self):
        htevents.write_key = None
        self.assertRaises(Exception, htevents.track)

    def test_no_host(self):
        htevents.host = None
        self.assertRaises(Exception, htevents.track)

    def test_track(self):
        htevents.track('userId', 'python module event')
        htevents.flush()

    def test_identify(self):
        htevents.identify('userId', {'email': 'user@email.com'})
        htevents.flush()

    def test_group(self):
        htevents.group('userId', 'groupId')
        htevents.flush()

    def test_alias(self):
        htevents.alias('previousId', 'userId')
        htevents.flush()

    def test_page(self):
        htevents.page('userId')
        htevents.flush()

    def test_screen(self):
        htevents.screen('userId')
        htevents.flush()

    def test_flush(self):
        htevents.flush()
