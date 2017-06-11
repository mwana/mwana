# vim: ai ts=4 sts=4 et sw=4
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule

_ = lambda s: s


class App(rapidsms.apps.base.AppBase):

    def start(self):
        self.schedule_notification_task()

    def schedule_notification_task(self):
        callback = 'mwana.apps.results_followup.tasks.send_email_alerts'

        # remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()

        EventSchedule.objects.create(callback=callback, days_of_week=[0, 1, 2, 3, 4],
                                     hours=[7], minutes=[30])


