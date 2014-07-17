# vim: ai ts=4 sts=4 et sw=4
import rapidsms

from rapidsms.contrib.scheduler.models import EventSchedule


# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that ./manage.py makemessages
# finds our text.
_ = lambda s: s


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
        EventSchedule.objects.create(callback=callback, hours=range(24),
                                     minutes=range(60))
