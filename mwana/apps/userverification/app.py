# vim: ai ts=4 sts=4 et sw=4
import logging

from mwana.apps.userverification.models import UserVerification
import rapidsms
from scheduler.models import EventSchedule
from datetime import datetime

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def start (self):
        self.schedule_send_verification_request_task()

    def schedule_send_verification_request_task(self):
        callback = 'mwana.apps.userverification.tasks.send_verification_request'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[9, 15], minutes=[20, 38],
                                     days_of_week=[0, 2, 3])

    def handle(self, message):
        """
        Handles user verification responses
        """
        contact = message.contact
        if not contact:
            return

        uv_records = UserVerification.objects.filter(contact=contact,
                                        facility=contact.location, request='1',
                                        verification_freq="A",
                                        responded=False)
        for uv in uv_records:
            uv.responded = True
            uv.response = message.text
            uv.response_date = datetime.today()
            uv.save()
        return bool(uv_records)