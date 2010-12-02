# vim: ai ts=4 sts=4 et sw=4
import logging
import rapidsms
from mwana.apps.labresults.messages import *
from rapidsms.contrib.scheduler.models import EventSchedule

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def start (self):
        self.schedule_endof_training_notification_task()


    def schedule_endof_training_notification_task(self):
        callback = 'mwana.apps.training.tasks.send_endof_training_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[16], minutes=[35],
                                     days_of_week=[0, 1, 2, 3, 4])

