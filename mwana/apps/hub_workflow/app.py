# vim: ai ts=4 sts=4 et sw=4
import logging
import rapidsms
from scheduler.models import EventSchedule
from mwana.apps.labresults.mocking import MockSMSReportsUtility

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def start (self):
        self.schedule_new_dbs_at_lab_notification_task()
        self.schedule_dbs_summary_to_hub_report_task()

    def handle(self, message):
        mocker = MockSMSReportsUtility()

        if mocker.handle(message):
            return True

    def schedule_new_dbs_at_lab_notification_task(self):
        callback = 'mwana.apps.hub_workflow.tasks.send_new_dbs_at_lab_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[16], minutes=[40],
                                     days_of_week=[3, 4])

    def schedule_dbs_summary_to_hub_report_task(self):
        callback = 'mwana.apps.hub_workflow.tasks.send_dbs_summary_to_hub_report'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[10, 14], minutes=[10],
                                     days_of_week=[0, 1, 2, 3, 4])
    