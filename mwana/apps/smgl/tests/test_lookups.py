"Test django-selectable lookup customizations."

from django.test.client import RequestFactory
from django.utils import simplejson as json

from django.utils.unittest.case import TestCase


from mwana.apps.locations.models import Location, LocationType
from mwana.apps.smgl import lookups
from mwana.apps.smgl.tests.shared import create_location


class LookupTestMixin(object):
    "Mixin for testing django-selectable lookups."

    lookup_class = None

    def get_query(self, **kwargs):
        factory = RequestFactory()
        request = factory.get(self.lookup_class.url(), kwargs)
        lookup = self.lookup_class()
        return json.loads(lookup.results(request).content)

    def assertInResults(self, item, results):
        self.assertTrue(any([item.pk == r['id'] for r in results['data']]))

    def assertNotInResults(self, item, results):
        self.assertFalse(any([item.pk == r['id'] for r in results['data']]))


class ProvinceLookupTestCase(LookupTestMixin, TestCase):
    "Lookup class for finding SMGL Provinces."

    lookup_class = lookups.ProvinceLookup

    def setUp(self):
        # Delete other existing markets loaded by fixtures
        Location.objects.all().delete()
        self.province1 = create_location(data={'name': 'prov1'})
        self.province2 = create_location(data={'name': 'prov2'})

    def test_find_by_name(self):
        "Find province by name (case insensitive)."
        results = self.get_query(term='Prov1')
        self.assertInResults(self.province1, results)
        self.assertNotInResults(self.province2, results)

    def test_find_all(self):
        "Get all provinces."
        results = self.get_query(term='')
        self.assertInResults(self.province1, results)
        self.assertInResults(self.province2, results)


class DistrictLookupTestCase(LookupTestMixin, TestCase):
    "Lookup class for finding SMGL Districts."

    lookup_class = lookups.DistrictLookup

    def setUp(self):
        # Delete other existing markets loaded by fixtures
        Location.objects.all().delete()
        self.province1 = create_location(data={'name': 'prov1'})
        loc_type = LocationType.objects.get(singular='district')
        self.district1 = create_location(data={'name': 'district1',
                                               'type': loc_type})
        self.district2 = create_location(data={'name': 'district2',
                                               'type': loc_type})

    def test_find_by_name(self):
        "Find district by name (case insensitive)."
        results = self.get_query(term='District1')
        self.assertInResults(self.district1, results)
        self.assertNotInResults(self.district2, results)

    def test_find_all(self):
        "Get all districts."
        results = self.get_query(term='')
        self.assertInResults(self.district1, results)
        self.assertInResults(self.district2, results)
        self.assertNotInResults(self.province1, results)


class FacilityLookupTestCase(LookupTestMixin, TestCase):
    "Lookup class for finding SMGL Districts."

    lookup_class = lookups.FacilityLookup

    def setUp(self):
        # Delete other existing markets loaded by fixtures
        Location.objects.all().delete()
        self.province1 = create_location(data={'name': 'prov1'})
        loc_type = LocationType.objects.get(singular='district')
        self.district1 = create_location(data={'name': 'district1',
                                               'type': loc_type})
        loc_type = LocationType.objects.get(singular='Rural Health Centre')
        self.fac1 = create_location(data={'name': 'fac1',
                                           'type': loc_type,
                                           'parent': self.district1
                                           })
        self.fac2 = create_location(data={'name': 'fac2',
                                          'type': loc_type,
                                          'parent': self.district1
                                           })

    def test_find_by_name(self):
        "Find facility by name (case insensitive)."
        results = self.get_query(term='Fac1')
        self.assertInResults(self.fac1, results)
        self.assertNotInResults(self.fac2, results)

    def test_find_all(self):
        "Get all facilities."
        results = self.get_query(term='')
        self.assertInResults(self.fac1, results)
        self.assertInResults(self.fac2, results)
        self.assertNotInResults(self.province1, results)
        self.assertNotInResults(self.district1, results)
