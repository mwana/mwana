from django.contrib.auth.models import User
from django.test.client import Client
from django.utils.unittest.case import TestCase

from mwana.apps.smgl.tests.shared import (create_mother, create_referral,
        create_facility_visit, create_reminder_notification,
        create_told_reminder)


class BaseStatisticsViewTestCase(TestCase):
    """
    Setup content for use in TestCases
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'pword')
        self.client.login(username='test', password='pword')


class NationalStatisticsTestCase(BaseStatisticsViewTestCase):
    """
    Test the statistics view
    """


class DistrictStatisticsTestCase(BaseStatisticsViewTestCase):
    """
    Test the district-stats view
    """


class ReminderStatsTestCase(BaseStatisticsViewTestCase):
    """
    Test the reminder-stats view
    """
    def setUp(self):
        super(ReminderStatsTestCase, self).setUp()
        self.mom = create_mother()
        self.referral = create_referral(data={'mother': self.mom})
        self.visit = create_facility_visit(data={'mother': self.mom})
        self.edd_reminder = create_reminder_notification('edd_14',
                                                data={'mother': self.mom}
                                                )
        self.nvd_reminder = create_reminder_notification('nvd',
                                                data={'mother': self.mom}
                                                )
        self.em_ref_reminder = create_reminder_notification('em_ref',
                                                data={'mother': self.mom}
                                                )
        self.edd_told = create_told_reminder('edd',
                                                data={'mother': self.mom}
                                                )
        self.nvd_told = create_told_reminder('nvd',
                                                data={'mother': self.mom}
                                                )
        self.ref_told = create_told_reminder('ref',
                                                data={'mother': self.mom}
                                                )

    def test_default_reminder_stats(self):
        response = self.client.get('/smgl/reminder-stats/')
        self.assertEqual(200, response.status_code)
        table = response.context['reminder_stats_table']
        for row in table.object_list:
            self.assertEqual(1, row['reminders'])
            self.assertEqual(1, row['told'])

    def test_no_reminders(self):
        self.edd_reminder.delete()
        self.nvd_reminder.delete()
        self.em_ref_reminder.delete()
        self.edd_told.delete()
        self.nvd_told.delete()
        self.ref_told.delete()
        response = self.client.get('/smgl/reminder-stats/')
        self.assertEqual(200, response.status_code)
        table = response.context['reminder_stats_table']
        for row in table.object_list:
            self.assertEqual(0, row['reminders'])
            self.assertEqual(0, row['told'])

    def test_no_tolds(self):
        self.edd_told.delete()
        self.nvd_told.delete()
        self.ref_told.delete()
        response = self.client.get('/smgl/reminder-stats/')
        self.assertEqual(200, response.status_code)
        table = response.context['reminder_stats_table']
        for row in table.object_list:
            self.assertEqual(1, row['reminders'])
            self.assertEqual(0, row['told'])
