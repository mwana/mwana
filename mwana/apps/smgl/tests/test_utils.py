from django.utils.unittest.case import TestCase
from mwana.apps.smgl.utils import to_time


class TestUtilities(TestCase):
    
    
    def testTimeFormats(self):
        for good in ["1530", "0000", "2359", "15:30", " 1530 "]:
            to_time(good)
        for bad in ["315", "00045", "foo", "2400", "1560"]:
            try:
                to_time(bad)
                self.fail("Time %s did not raise an exception!" % bad)
            except ValueError:
                pass # good