from django.contrib.auth.models import User
from django.test.client import Client
from django.test import TestCase

from mwana.apps.smgl.tests.shared import (create_mother, create_told_reminder,
        create_reminder_notification)


class BaseStatisticsViewTestCase(TestCase):
    """
    Setup content for use in TestCases
    """
    def setUp(self):
        self.client = Client()
        try:
            self.user = User.objects.get(username='test')
        except User.DoesNotExist:
            self.user = User.objects.create_user('test', 'test@test.com', 'pword')
        self.client.login(username='test', password='pword')


#class NationalStatisticsTestCase(BaseStatisticsViewTestCase):
#    """
#    Test the statistics view
#    """
#
#
#class DistrictStatisticsTestCase(BaseStatisticsViewTestCase):
#    """
#    Test the district-stats view
#    """


class ReminderStatsTestCase(BaseStatisticsViewTestCase):
    """
    Test the reminder-stats view
    """
    def setUp(self):
        super(ReminderStatsTestCase, self).setUp()
        self.mom = create_mother()

    def test_default_reminder_stats(self):
        create_reminder_notification('edd_14',
                                    data={'mother': self.mom}
                                    )
        create_reminder_notification('nvd',
                                    data={'mother': self.mom}
                                    )
        create_reminder_notification('em_ref',
                                    data={'mother': self.mom}
                                    )
        create_told_reminder('edd',
                            data={'mother': self.mom}
                            )
        create_told_reminder('nvd',
                            data={'mother': self.mom}
                            )
        create_told_reminder('ref',
                            data={'mother': self.mom}
                            )
        response = self.client.get('/smgl/reminder-stats/')
        self.assertEqual(200, response.status_code)
        table = response.context['reminder_stats_table']
        for row in table.object_list:
            self.assertEqual(1, row['reminders'])
            self.assertEqual(1, row['told'])

    def test_no_reminders(self):
        response = self.client.get('/smgl/reminder-stats/')
        self.assertEqual(200, response.status_code)
        table = response.context['reminder_stats_table']
        for row in table.object_list:
            self.assertEqual(0, row['reminders'])
            self.assertEqual(0, row['told'])

    def test_no_tolds(self):

        create_reminder_notification('edd_14',
                                    data={'mother': self.mom}
                                    )
        create_reminder_notification('nvd',
                                    data={'mother': self.mom}
                                    )
        create_reminder_notification('em_ref',
                                    data={'mother': self.mom}
                                    )
        response = self.client.get('/smgl/reminder-stats/')
        self.assertEqual(200, response.status_code)
        table = response.context['reminder_stats_table']
        for row in table.object_list:
            self.assertEqual(1, row['reminders'])
            self.assertEqual(0, row['told'])
