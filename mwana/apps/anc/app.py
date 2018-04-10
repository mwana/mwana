# vim: ai ts=4 sts=4 et sw=4
import rapidsms
from datetime import datetime
import time

from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Connection

from mwana.apps.anc.messages import WELCOME_MSG_A
from mwana.apps.anc.messages import WELCOME_MSG_B
from mwana.apps.anc.models import FlowClientRegistration
from mwana.apps.anc.models import CommunityWorker
from mwana.apps.locations.models import Location
from mwana.apps.anc.models import FlowCommunityWorkerRegistration
from mwana.apps.anc.messages import MISCARRIAGE_MSG, STILL_BITH_MSG
from mwana.apps.anc.models import WaitingForResponse
from mwana.apps.anc.models import Client
from mwana.util import LocationCode

_ = lambda s: s
# TODO: configure supported numbers in database
SUPPORTED_PHONE_LINES = ['97', '96']
INVALID_PHONE_NUMBER_RESPONSE = "Sorry %(number)s is not a valid Airtel or MTN number. Reply with correct number"


class App(rapidsms.apps.base.AppBase):
    def start(self):
        self.schedule_notification_task()

    def valid_phone(self, text):
        try:
            int(text)
        except ValueError:
            return None
        if len(text) not in (len('+260979123456'), len('260979123456'), len('0979123456'),
                             len('979123456')):
            return None
        if text[-9:-7] not in SUPPORTED_PHONE_LINES:
            return None
        return '+260' + text[-9:]

    def schedule_notification_task(self):
        """
        Resets (removes and re-creates) the task in the scheduler app that is
        used to send notifications to CBAs.
        """

        callback = 'mwana.apps.anc.tasks.send_anc_messages'

        # remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()

        # TODO: modify after testing window
        EventSchedule.objects.create(callback=callback, hours=range(6, 18),
                                     minutes=range(0, 60, 5))

    def handle(self, msg):
        if not msg.text:
            return False

        # mocker = MockANCUtility()
        #
        # if mocker.handle(msg):
        #     return True

        cleaned_text = msg.text.strip().lower()[:30]
        #-------------------------#
        # Handle CHW Registration #
        #-------------------------#
        open_flows = FlowCommunityWorkerRegistration.objects.filter(connection=msg.connection, open=True,
                                                                    start_time__lte=datetime.now()). \
            filter(valid_until__gte=datetime.now())

        if open_flows:
            flow = FlowCommunityWorkerRegistration.objects.filter(connection=msg.connection, open=True,
                                                                  start_time__lte=datetime.now()). \
                get(valid_until__gte=datetime.now())
            if not flow.name:
                flow.name = cleaned_text.title()
                flow.save()
                msg.respond("Thank you %s. Now reply with your clinic code" % flow.name)
                return True
            elif not flow.facility:
                clinic_code = LocationCode(cleaned_text)
                location_type = clinic_code.get_location_type()
                locations = Location.objects.filter(slug__iexact=cleaned_text[:6],
                                                    type__slug__in=location_type)
                if not locations:
                    msg.respond(
                        ("Sorry, I don't know about a clinic with code %(code)s. "
                         "Please check your code and try again."),
                        code=cleaned_text)
                    return True
                flow.facility = locations[0]

                flow.save()
                chw = CommunityWorker()
                chw.connection = flow.connection
                chw.name = flow.name
                chw.facility = flow.facility
                chw.is_active = True

                chw.save()
                flow.delete()
                msg.respond("%(name)s you have successfully joined as CHW for the Mother Baby Service Reminder Program "
                            "from %(clinic)s clinic. If this is not correct send 555555 and register again",
                            name=chw.name, clinic=chw.facility.name)
                return True

        #--------------------------------#
        # Handle ANC Client Registration #
        #--------------------------------#
        open_flows = FlowClientRegistration.objects.filter(community_worker__connection=msg.connection, open=True,
                                                           start_time__lte=datetime.now()). \
            filter(valid_until__gte=datetime.now())

        if open_flows:
            flow = FlowClientRegistration.objects.filter(community_worker__connection=msg.connection, open=True,
                                                         start_time__lte=datetime.now()). \
                get(valid_until__gte=datetime.now())
            if not flow.phone:
                phone = self.valid_phone(cleaned_text)
                if not phone:
                    msg.respond(INVALID_PHONE_NUMBER_RESPONSE, number=cleaned_text)
                    return True
                flow.phone = phone
                flow.save()
                msg.respond(
                    "You have submitted mum's phone number %s. Now reply with the mum's gestational age in weeks" % flow.phone)
                return True
            elif not flow.gestation_at_subscription:
                try:
                    _age = cleaned_text.replace('weeks', '').replace('week', '').replace('wks', '').replace('weaks',
                                                                                                            ''). \
                        replace('weak', '').replace('wk', '').strip()
                    flow.gestation_at_subscription = abs(int(_age))
                    if flow.gestation_at_subscription > 60:
                        msg.respond(
                            "Sorry %s gestational age is too much. You cannot register a"
                            " mother's pregnancy when gestational age is already 40 or above" % flow.gestation_at_subscription)
                        return True
                    elif flow.gestation_at_subscription >= 40:
                        msg.respond(
                            "Sorry you cannot register a mother's pregnancy when gestational age is already 40 or above")
                        return True
                    flow.save()
                    msg.respond("Mother's phone number is %(phone)s and gestational age is %(age)s. Reply with Yes if "
                                "this is correct or No if not", phone=flow.phone, age=flow.gestation_at_subscription)
                    return True
                except ValueError:
                    msg.respond("Sorry %s is not a valid gestational age. Enter a valid number" % cleaned_text)
                    return True
            elif cleaned_text in ('yes', 'y'):
                clients = Client.objects.filter(connection__identity=flow.phone, is_active=True,
                                                lmp__gte=Client.find_lmp(40))

                phone_start = flow.phone[:6]
                if msg.connection.identity.startswith(phone_start):
                    backend = msg.connection.backend
                else:
                    msgs = Message.objects.filter(connection__identity__startswith=phone_start).order_by('-date')
                    backend = msgs[0].connection.backend
                client_connection, _ = Connection.objects.get_or_create(backend=backend, identity=flow.phone)

                # TODO: ensure there is only one such record at a time
                if clients:
                    client = clients[0]
                    client.gestation_at_subscription = flow.gestation_at_subscription
                    client.lmp = Client.find_lmp(flow.gestation_at_subscription)
                    client.facility = flow.community_worker.facility

                    client.connection = client_connection
                    client.status = 'pregnant'
                    client.save()
                else:
                    client = Client.objects.create(gestation_at_subscription=flow.gestation_at_subscription,
                                                   lmp=Client.find_lmp(flow.gestation_at_subscription),
                                                   facility=flow.community_worker.facility,
                                                   connection=client_connection)

                msg.respond("You have successfully registered %(age)s week pregnant mother with phone number "
                            "%(phone)s", age=flow.gestation_at_subscription, phone=flow.phone)
                client.age_confirmed = False
                client.community_worker = flow.community_worker
                client.save()
                time.sleep(3)
                other_age = flow.gestation_at_subscription + 1
                if flow.gestation_at_subscription >= 39:
                    other_age = flow.gestation_at_subscription - 1
                OutgoingMessage(client.connection, WELCOME_MSG_A, age=flow.gestation_at_subscription, other_age=other_age).send()
                flow.delete()
                return True
            elif cleaned_text in ('no', 'n'):
                msg.respond("You can start a new submission by sending ANC")
                flow.delete()
                return True
            else:
                msg.respond("Mother's phone number is %(phone)s and gestational age is %(age)s. Reply with Yes if "
                            "this is correct or No if not", phone=flow.phone, age=flow.gestation_at_subscription)
                return True


        if cleaned_text.startswith('yes') and Client.objects.filter(connection=msg.connection,
                                                                    is_active=True, phone_confirmed=False):
            for client_record in Client.objects.filter(connection=msg.connection,
                                                       is_active=True, phone_confirmed=False):
                client_record.phone_confirmed = True
                client_record.save()
            msg.respond(WELCOME_MSG_B)
            return True
        elif cleaned_text.startswith('no') and Client.objects.filter(connection=msg.connection,
                                                                    is_active=True, phone_confirmed=False):
            for client_record in Client.objects.filter(connection=msg.connection,
                                                       is_active=True, phone_confirmed=False):
                client_record.is_active = False
                client_record.status = 'refused'
                client_record.save()
            msg.respond("Thank you.")
            return True

        waitingForResponses = WaitingForResponse.objects.filter(client_gestation__connection=msg.connection,
                                                                response=None)
        if waitingForResponses:
            for record in waitingForResponses:
                client_gestation = record.client_gestation
                if msg.text.strip() == '1':
                    client_gestation.status = 'miscarriage'
                elif msg.text.strip() == '2':
                    client_gestation.status = 'stillbirth'
                else:
                    client_gestation.status = 'stop'
                client_gestation.save()
                record.response = msg.text.strip()
                record.save()
            if msg.text.strip() == '1':
                msg.respond(MISCARRIAGE_MSG)
            elif msg.text.strip() == '2':
                msg.respond(STILL_BITH_MSG)
            else:
                msg.respond("Thank you")
            return True

        # Unknown message from client/mother
        if Client.objects.filter(connection=msg.connection).exists():
            msg.respond("For emergencies contact your local clinic")
            return True
        if CommunityWorker.objects.filter(connection=msg.connection).exists():
            msg.respond("Sorry, the system could not understand your message.")
            return True

        return False
