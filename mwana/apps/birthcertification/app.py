# vim: ai ts=4 sts=4 et sw=4
import logging
from mwana.apps.alerts.app import mwana
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule



logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def start (self):
        self.schedule_birth_registration_reminder_task()
        self.schedule_send_certicate_ready_notification_task()

    def schedule_birth_registration_reminder_task(self):
        callback = 'mwana.apps.birthcertification.tasks.send_birth_registration_reminder'
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[14, 15, 16, 17, 18], minutes=range(60),
                                     days_of_week=[0, 1, 2, 3, 4, 5, 6])
                                     
    def schedule_send_certicate_ready_notification_task(self):
        callback = 'mwana.apps.birthcertification.tasks.send_certicate_ready_notification'
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[14, 15, 16, 17, 18], minutes=range(60),
                                     days_of_week=[0, 1, 2, 3, 4, 5, 6])
