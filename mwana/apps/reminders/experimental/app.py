# vim: ai ts=4 sts=4 et sw=4
import rapidsms

from rapidsms.contrib.scheduler.models import EventSchedule


class App(rapidsms.apps.base.AppBase):   
   
    def start(self):
        self.schedule_notification_task()
    
    def schedule_notification_task (self):
        """
        Resets (removes and re-creates) the task in the scheduler app that is
        used to send notifications to CBAs.
        """
        callback = 'mwana.apps.reminders.experimental.tasks.send_notifications_to_clinic'
        
        #remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()
#        EventSchedule.objects.create(callback=callback, hours=[7, 9], minutes=[51],
#                                     days_of_week=[0, 1, 2, 3, 4])
