# vim: ai ts=4 sts=4 et sw=4
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule

from mwana.apps.anc.mocking import MockANCUtility
from mwana.apps.anc.models import Client

_ = lambda s: s


class App(rapidsms.apps.base.AppBase):

    def start(self):
        self.schedule_notification_task()

    def schedule_notification_task(self):
        """
        Resets (removes and re-creates) the task in the scheduler app that is
        used to send notifications to CBAs.
        """

        callback = 'mwana.apps.anc.tasks.send_anc_messages'

        # remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()
        # EventSchedule.objects.create(callback=callback, hours=[6, 15],
        #                              minutes=[5])
        EventSchedule.objects.create(callback=callback, hours=range(24),
                                     minutes=range(60))

    def handle(self, msg):

        mocker = MockANCUtility()

        if mocker.handle(msg):
            return True

        if not Client.objects.filter(connection=msg.connection).exists():
            return False
        if not msg.text:
            return True
        msg.respond("Received")

        return True
