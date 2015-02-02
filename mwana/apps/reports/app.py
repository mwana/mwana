# vim: ai ts=4 sts=4 et sw=4
import logging
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule
from mwana.apps.labresults.mocking import MockSMSReportsUtility

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def start (self):
        self.schedule_eid_and_birth_dho_report_task()
        self.schedule_eid_and_birth_pho_report_task()
        self.schedule_send_cba_birth_report_task()
        self.schedule_send_cba_encouragement_task()
        self.schedule_build_messages_report_task()
        self.schedule_build_msg_by_backend_rpt_task()
        self.schedule_build_scaleup_sites_task()

    def handle(self, message):
        mocker = MockSMSReportsUtility()

        if mocker.handle(message):
            return True

    def schedule_eid_and_birth_dho_report_task(self):
        callback = 'mwana.apps.reports.tasks.send_dho_eid_and_birth_report'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[10], minutes=[20],
                                     days_of_week=[0, 1, 2, 3, 4])

    def schedule_eid_and_birth_pho_report_task(self):
        callback = 'mwana.apps.reports.tasks.send_pho_eid_and_birth_report'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[10], minutes=[15],
                                     days_of_week=[0, 1, 2, 3, 4])


    def schedule_send_cba_birth_report_task(self):
        callback = 'mwana.apps.reports.tasks.send_cba_birth_report'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[8, 14], minutes=range(0, 50, 5),
                                     days_of_week=[0, 1, 2, 3, 4])

    def schedule_send_cba_encouragement_task(self):
        callback = 'mwana.apps.reports.tasks.send_cba_encouragement'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[9,15], minutes=range(0, 50, 5),
                                     days_of_week=[0, 1, 2, 3, 4])

    def schedule_build_messages_report_task(self):
        callback = 'mwana.apps.reports.tasks.build_messages_report'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[6, 15], minutes=[0],
                                     days_of_week=[0, 1, 2, 3, 4, 5, 6])

    def schedule_build_msg_by_backend_rpt_task(self):
        callback = 'mwana.apps.reports.tasks.build_msg_by_backend_rpt'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[18], minutes=[0],
                                     days_of_week=[0, 1, 2, 3, 4, 5, 6])

    def schedule_build_scaleup_sites_task(self):
        callback = 'mwana.apps.reports.tasks.build_scaleup_sites'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[7, 10, 12, 14, 17], minutes=[30],
                                     days_of_week=[0, 1, 2, 3, 4, 5, 6])
