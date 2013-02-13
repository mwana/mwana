# vim: ai ts=4 sts=4 et sw=4
import logging

from mwana.apps.userverification.models import UserVerification
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule
from datetime import datetime
from rapidsms.models import Connection

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def start (self):
        self.schedule_send_verification_request_task()
        self.schedule_send_final_verification_request_task()
        self.schedule_inactivate_lost_users_task()

    def schedule_send_verification_request_task(self):
        callback = 'mwana.apps.userverification.tasks.send_verification_request'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[9, 15], minutes=[20, 38],
                                     days_of_week=[0, 1, 2, 3])

    def schedule_send_final_verification_request_task(self):
        callback = 'mwana.apps.userverification.tasks.send_final_verification_request'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[9, 15], minutes=[40, 48],
#                                     days_of_week=[0, 1, 2, 3])
                                     days_of_week=[6])

    def schedule_inactivate_lost_users_task(self):
        callback = 'mwana.apps.userverification.tasks.inactivate_lost_users'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[6, 18], minutes=[15],
#                                     days_of_week=[2, 4, 5, 6])
                                     days_of_week=[0])

    def handle(self, message):
        """
        Handles user verification responses
        """
        contact = message.contact
        if not contact:
            return

        if message.text and message.text.upper().strip() == 'NO':
            contact.is_active = False
            contact.save()
            conn= Connection.objects.get(contact=contact)
            conn.contact = None
            conn.save()


        uv_records = UserVerification.objects.filter(contact=contact,
                                        facility=contact.location, request__in=['1', '2'],
                                        verification_freq__in=['A', 'F'],
                                        responded=False)
        for uv in uv_records:
            uv.responded = True
            uv.response = message.text
            uv.response_date = datetime.today()
            uv.save()
        return bool(uv_records)