from django.utils.unittest.case import TestCase

from mwana.apps.locations.models import LocationType

from mwana.apps.smgl.utils import to_time, get_current_district
from mwana.apps.smgl.tests.shared import create_location


class BaseStatisticsViewTestCase(TestCase):
    """
    Setup content for user in TestCases
    """
    def setUp()


class NationalStatisticsTestCase(BaseStatisticsViewTestCase):
    """
    Test the statistics view
    """



class NationalStatisticsTestCase(BaseStatisticsViewTestCase):
    """
    Test the district-stats view
    """

