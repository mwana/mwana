# vim: ai ts=4 sts=4 et sw=4
import logging
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule
from mwana.apps.labresults.mocking import MockSMSReportsUtility

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def start (self):
        self.schedule_eid_and_birth_dho_report_task()
        self.schedule_eid_and_birth_dho_report_task()

    def handle(self, message):
        mocker = MockSMSReportsUtility()

        if mocker.handle(message):
            return True

    def schedule_eid_and_birth_dho_report_task(self):
        callback = 'mwana.apps.reports.tasks.send_dho_eid_and_birth_report'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[10, 14], minutes=[20],
                                     days_of_week=[0, 1, 2, 3, 4])
    def schedule_eid_and_birth_dho_report_task(self):
        callback = 'mwana.apps.reports.tasks.send_pho_eid_and_birth_report'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[10, 14], minutes=[15],
                                     days_of_week=[0, 1, 2, 3, 4])

    