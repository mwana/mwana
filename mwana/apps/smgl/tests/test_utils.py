from django.utils.unittest.case import TestCase

from mwana.apps.locations.models import LocationType

from mwana.apps.smgl.utils import to_time, get_current_district
from mwana.apps.smgl.tests.shared import create_location


class TestUtilities(TestCase):

    def testTimeFormats(self):
        for good in ["1530", "0000", "2359", "15:30", " 1530 "]:
            to_time(good)
        for bad in ["315", "00045", "foo", "2400", "1560"]:
            try:
                to_time(bad)
                self.fail("Time %s did not raise an exception!" % bad)
            except ValueError:
                pass  # good

    def testCurrentDistrict(self):
        """
        ensure the utility returns a district or None
        """
        loc_type = LocationType.objects.get(singular='district')
        loc1 = create_location(data={'name': 'foo',
                                     'type': loc_type
                                     }
                              )
        loc_type = LocationType.objects.get(singular='Rural Health Centre')
        facility = create_location(data={'name': 'foo',
                                         'type': loc_type,
                                         'parent': loc1}
                                   )
        province = create_location()
        facility_district = get_current_district(facility)
        self.assertEqual(facility_district, loc1)
        loc1_district = get_current_district(loc1)
        self.assertEqual(loc1_district, loc1)
        province_district = get_current_district(province)
        self.assertEqual(province_district, None)
