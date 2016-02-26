# vim: ai ts=4 sts=4 et sw=4
import logging
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):

    def start (self):
        # TODO: uncomment next line to enable the tasks
        self.schedule_clinics_not_retrieving_results_alerts_task()
        self.schedule_clinics_not_sending_dbs_alerts_task()
        self.schedule_hubs_not_sending_dbs_alerts_task()

    def schedule_clinics_not_retrieving_results_alerts_task(self):
        callback = 'mwana.apps.alerts.tasks.send_clinics_not_retrieving_results_alerts'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        # TODO: uncomment next line to enable the task
#        EventSchedule.objects.create(callback=callback, hours=[14], minutes=[5],
#                                     days_of_week=[0, 1, 2, 3, 4])

    def schedule_clinics_not_sending_dbs_alerts_task(self):
        callback = 'mwana.apps.alerts.tasks.send_clinics_not_sending_dbs_alerts'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        # TODO: uncomment next line to enable the task
#        EventSchedule.objects.create(callback=callback, hours=[14], minutes=[10],
#                                     days_of_week=[0, 1, 2, 3, 4])

    def schedule_hubs_not_sending_dbs_alerts_task(self):
        callback = 'mwana.apps.alerts.tasks.send_hubs_not_sending_dbs_alerts'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        # TODO: uncomment next line to enable the task
#        EventSchedule.objects.create(callback=callback, hours=[14], minutes=[15],
#                                     days_of_week=[0, 1, 2, 3, 4])
