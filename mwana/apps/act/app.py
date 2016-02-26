# vim: ai ts=4 sts=4 et sw=4
from rapidsms.contrib.scheduler.models import EventSchedule
import rapidsms

class App (rapidsms.apps.base.AppBase):
    def start(self):
        self.schedule_notification_task()

    def schedule_notification_task (self):
        """
        Resets (removes and re-creates) the task in the scheduler app that is
        used to send notifications to CBAs.
        """
        callback = 'mwana.apps.act.tasks.send_notifications'

        #remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=range(24),
                                     minutes=range(60))