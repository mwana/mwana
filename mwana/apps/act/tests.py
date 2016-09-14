# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import ReminderMessagePreference
from mwana.apps.act.models import HistoricalEvent
from mwana.apps.act.models import SentReminder
from mwana.apps.act.models import ReminderDay
from mwana.apps.act.models import RemindersSwitch
from mwana.apps.act.models import Appointment
from mwana.apps.act.models import CHW
from mwana.apps.act import tasks
import json

import datetime
from datetime import timedelta
from datetime import date
import time
import mwana.const as const
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Connection, Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.act.models import Client
from mwana.apps.act.models import Payload
from mwana.apps.act.testdata.payloads import CLIENT_PAYLOAD
from mwana.apps.act.testdata.payloads import CHW_PAYLOAD
from mwana.apps.act.testdata.payloads import LAB_APPOINTMENT_PAYLOAD
from mwana.apps.act.testdata.payloads import PHARMACY_APPOINTMENT_PAYLOAD


class ActSetUp(TestScript):
    def setUp(self):
        # this call is required if you want to override setUp
        super(ActSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[
            0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="luapula")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="mansa", parent=self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya",
                                              parent=self.luapula)
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="402029", parent=self.samfya,
                                              send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012",
                                                     parent=self.mansa, send_live_results=True)
        # clinic for send_live_results = True
        self.clinic_live_results_true = Location.objects.create(type=self.type, name="LiveResultsTrue Clinic",
                                                                slug="403010", parent=self.mansa,
                                                                send_live_results=True)
        # clinic for send_live_results = False
        self.clinic_live_results_false = Location.objects.create(type=self.type, name="LiveResultsFalse Clinic",
                                                                 slug="403011", parent=self.mansa,
                                                                 send_live_results=False)

        self.support_clinic = Location.objects.create(type=self.type, name="Support Clinic", slug="spt")
        # this gets the backend and connection in the db
        script = "clinic_worker > hello world"
        self.runScript(script)
        connection = Connection.objects.get(identity="clinic_worker")

        self.contact = Contact.objects.create(alias="banda", name="John Banda",
                                              location=self.clinic, pin="4567")
        self.contact.types.add(const.get_clinic_worker_type())

        connection.contact = self.contact
        connection.save()

        # create another one
        self.other_contact = Contact.objects.create(alias="mary", name="Mary Phiri",
                                                    location=self.clinic, pin="6789")
        self.other_contact.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="other_worker", backend=connection.backend,
                                  contact=self.other_contact)
        connection.save()

        # create another worker for a different clinic
        self.central_clinic_worker = Contact.objects.create(alias="jp", name="James Phiri",
                                                            location=self.mansa_central, pin="1111")
        self.central_clinic_worker.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="central_clinic_worker", backend=connection.backend,
                                  contact=self.central_clinic_worker)
        connection.save()

        # create a worker for the live_results_true clinic
        self.true_clinic_worker = Contact.objects.create(alias="jbt", name="John Banda",
                                                         location=self.clinic_live_results_true, pin="1001")
        self.true_clinic_worker.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="true_clinic_worker", backend=connection.backend,
                                  contact=self.true_clinic_worker)

        # create a worker for the live_results_false clinic
        self.false_clinic_worker = Contact.objects.create(alias="jbf", name="John Banda",
                                                          location=self.clinic_live_results_false, pin="0110")
        self.false_clinic_worker.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="false_clinic_worker", backend=connection.backend,
                                  contact=self.false_clinic_worker)

        # create support staff
        self.support_contact = Contact.objects.create(alias="ha1", name="Help Admin",
                                                      location=self.support_clinic, pin="1111", is_help_admin=True)
        self.support_contact.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="support_contact", backend=connection.backend,
                                  contact=self.support_contact)
        connection.save()

        # create second support staff
        self.support_contact2 = Contact.objects.create(alias="ha2", name="Help Admin2",
                                                       location=self.support_clinic, pin="2222", is_help_admin=True)
        self.support_contact2.types.add(const.get_clinic_worker_type())

        Connection.objects.create(identity="support_contact2", backend=connection.backend,
                                  contact=self.support_contact2)
        connection.save()

    def tearDown(self):
        # this call is required if you want to override tearDown
        super(ActSetUp, self).tearDown()
        try:
            self.clinic.delete()
            self.type.delete()
            self.client.logout()
        except:
            pass
            #TODO catch specific exception

    def testBootstrap(self):
        contact = Contact.objects.get(id=self.contact.id)
        self.assertEqual("clinic_worker", contact.default_connection.identity)
        self.assertEqual(self.clinic, contact.location)
        self.assertEqual("4567", contact.pin)
        self.assertTrue(const.get_clinic_worker_type() in contact.types.all())


class TestPayloadAcceptor(ActSetUp):
    """
    Tests processing of payloads
    """

    def _post_json(self, url, data):
        if not isinstance(data, basestring):
            data = json.dumps(data)
        return self.client.post(url, data, content_type='text/json')

    def test_client_payload_entry(self):
        self.create_payload_auther_login()

        now = datetime.datetime.now()
        response = self._post_json(reverse('act:accept_appointments'), CLIENT_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payload.objects.count(), 1)
        payload = Payload.objects.get()
        # self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        # self.assertEqual(user, payload.auth_user)
        self.assertEqual(payload.incoming_date.year, now.year)
        self.assertEqual(payload.incoming_date.month, now.month)
        self.assertEqual(payload.incoming_date.day, now.day)
        self.assertEqual(payload.incoming_date.hour, now.hour)

        self.assertEqual(Client.objects.count(), 1)
        client = Client.objects.get()
        # @type client Client
        self.assertEqual(client.sex, 'm')
        self.assertEqual(client.national_id, '12313131')
        self.assertEqual(client.uuid, 'f9f7ce6f-050f-40f3-b904-d49b60539c58')
        self.assertEqual(client.phone, '+260979236339')
        self.assertEqual(client.location.slug, '402029')

    def test_chw_payload_entry(self):
        self.create_payload_auther_login()

        now = datetime.datetime.now()
        response = self._post_json(reverse('act:accept_appointments'), CHW_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payload.objects.count(), 1)
        payload = Payload.objects.get()
        # self.assertEqual(payload.raw, json.dumps(data))
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)
        # self.assertEqual(user, payload.auth_user)
        self.assertEqual(payload.incoming_date.year, now.year)
        self.assertEqual(payload.incoming_date.month, now.month)
        self.assertEqual(payload.incoming_date.day, now.day)
        self.assertEqual(payload.incoming_date.hour, now.hour)

        self.assertEqual(CHW.objects.count(), 1)
        record = CHW.objects.get()
        # @type record CHW
        self.assertEqual(record.name, 'Trevor Sinkala')
        self.assertEqual(record.national_id, '1321313')
        self.assertEqual(record.uuid, 'd3ee80b7-67e6-423b-9db5-a34a79a2c01a')
        self.assertEqual(record.phone, '+260979599999')
        self.assertEqual(record.location.slug, '402029')
        self.assertEqual(record.address, 'Kwatu. (Zone 1)')

    def test_workflow(self):
        self.create_payload_auther_login()

        now = datetime.datetime.now()
        response = self._post_json(reverse('act:accept_appointments'), CLIENT_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        response = self._post_json(reverse('act:accept_appointments'), CHW_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        response = self._post_json(reverse('act:accept_appointments'), LAB_APPOINTMENT_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        response = self._post_json(reverse('act:accept_appointments'), PHARMACY_APPOINTMENT_PAYLOAD)
        self.assertEqual(response.status_code, 200)

        payload = Payload.objects.get(pk=3)
        self.assertTrue(payload.parsed_json)
        self.assertTrue(payload.validated_schema)

        self.assertEqual(payload.incoming_date.hour, now.hour)

        self.assertEqual(Appointment.objects.filter(type=Appointment.get_pharmacy_type()).count(), 1)
        self.assertEqual(Appointment.objects.filter(type=Appointment.get_lab_type()).count(), 1)
        self.assertEqual(Appointment.objects.filter(status='pending', type=Appointment.get_lab_type()).count(), 1)
        record = Appointment.objects.get(type=Appointment.get_lab_type())
        # @type record Appointment
        appointment_date = date.today() + timedelta(days=7)
        self.assertEqual(record.date, appointment_date)
        self.assertEqual(record.uuid, 'f5936299-f07a-49d0-9145-c2fcb8458a28')
        self.assertEqual(record.type, Appointment.get_lab_type())
        self.assertEqual(record.client.phone, '+260979236339')
        self.assertEqual(record.cha_responsible.phone, '+260979599999')

        script = '''
            +260979599999 > ACT YES
            +260979599999 < Thank you
            +260979236339 > Act yes
            +260979236339 < Thank you
        '''
        self.runScript(script)

        client = Client.objects.get()

        self.assertEqual(client.connection.identity, '+260979236339')
        self.assertEqual(client.can_receive_messages, True, "Can't receive messages")
        self.assertEqual(client.phone_verified, True, 'Phone is not verified')
        self.assertEqual(client.is_eligible_for_messaging(), True)

        # TODO: Add client to error ignore list

        time.sleep(.2)
        # start router and attempt to send notifications
        self.startRouter()
        tasks.send_notifications(self.router)

        # Get all the messages sent
        # reminders still not turned on
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(0, len(msgs))

        # turn on reminders
        RemindersSwitch.objects.create()
        # configure reminder for lab visits
        ReminderDay.objects.create(appointment_type=Appointment.get_lab_type(), days=7)

        time.sleep(.2)
        self.startRouter()
        tasks.send_notifications(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(2, len(msgs))

        msg1 = "Time up %s" % appointment_date.strftime('%d/%m/%Y')
        msg2 = "Hello Trevor Sinkala. TK-14141414141 is due for Lab Visit on %s." % appointment_date.strftime(
            '%d/%m/%Y')
        self.assertTrue(msg1 in [msg.text for msg in msgs], msg1 + " not in " + ", ".join(msg.text for msg in msgs))
        self.assertTrue(msg2 in [msg.text for msg in msgs], msg2 + " not in " + ", ".join(msg.text for msg in msgs))

        self.assertEqual(Appointment.objects.filter(status='pending').count(), 1)
        self.assertEqual(Appointment.objects.filter(status='notified').count(), 1)

        # messages should not be sent again
        time.sleep(.2)
        self.startRouter()
        tasks.send_notifications(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(0, len(msgs), 'messages should not be sent again')

        # fake that reminders have not been sent
        SentReminder.objects.all().delete()

        HistoricalEvent.objects.create(date=appointment_date, fact_message="Jonah was swallowed")
        # control pharmacy message
        rmp = ReminderMessagePreference.objects.get(client=client, visit_type=Appointment.get_lab_type())
        # @type rmp ReminderMessagePreference
        rmp.message_id = 'm7'
        rmp.save()

        self.startRouter()
        tasks.send_notifications(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(2, len(msgs))

        msg1 = "Did you know? On %s Jonah was swallowed" % appointment_date.strftime('%d %B')
        msg2 = "Hello Trevor Sinkala. TK-14141414141 is due for Lab Visit on %s." % appointment_date.strftime(
            '%d/%m/%Y')
        self.assertTrue(msg1 in [msg.text for msg in msgs], msg1 + " not in " + ", ".join(msg.text for msg in msgs))
        self.assertTrue(msg2 in [msg.text for msg in msgs], msg2 + " not in " + ", ".join(msg.text for msg in msgs))

        # fake that reminders have not been sent
        SentReminder.objects.all().delete()

        # @type client Client
        rmp = ReminderMessagePreference.objects.get(client=client, visit_type=Appointment.get_lab_type())
        rmp.message_id = 'm4'
        rmp.save()

        self.startRouter()
        tasks.send_notifications(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(2, len(msgs))

        msg1 = "One Zambia one nation. %s" % appointment_date.strftime('%d/%m/%Y')
        msg2 = "Hello Trevor Sinkala. TK-14141414141 is due for Lab Visit on %s." % appointment_date.strftime(
            '%d/%m/%Y')
        self.assertTrue(msg1 in [msg.text for msg in msgs], msg1 + " not in " + ", ".join(msg.text for msg in msgs))
        self.assertTrue(msg2 in [msg.text for msg in msgs], msg2 + " not in " + ", ".join(msg.text for msg in msgs))

        # configure reminder for pharmacy visits
        ReminderDay.objects.create(appointment_type=Appointment.get_pharmacy_type(), days=14)

        time.sleep(.2)
        self.startRouter()
        tasks.send_notifications(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(2, len(msgs))

        appointment_date = date.today() + timedelta(days=14)
        msg1 = "Good day. Happy day %s" % appointment_date.strftime('%d/%m/%Y')
        msg2 = "Hello Trevor Sinkala. TK-14141414141 is due for Pharmacy Visit on %s." % appointment_date.strftime(
            '%d/%m/%Y')
        self.assertTrue(msg1 in [msg.text for msg in msgs], msg1 + " not in " + ", ".join(msg.text for msg in msgs))
        self.assertTrue(msg2 in [msg.text for msg in msgs], msg2 + " not in " + ", ".join(msg.text for msg in msgs))

        self.assertEqual(Appointment.objects.filter(status='notified').count(), 2)


    def test_payload_login_required(self):
        data = {'varname': 'data'}
        response = self._post_json(reverse('act:accept_appointments', ), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(Payload.objects.count(), 0)

    def test_payload_permission_required(self):
        User.objects.create_user(username='adh', email='', password='abc')
        self.client.login(username='adh', password='abc')
        data = {'varname': 'data'}
        response = self._post_json(reverse('act:accept_appointments'), data)
        self.assertEqual(response.status_code, 401) # authorization required
        self.assertEqual(Payload.objects.count(), 0)

    def test_payload_post_required(self):
        response = self.client.get(reverse('act:accept_appointments'))
        self.assertEqual(response.status_code, 405) # method not supported

    def create_payload_auther_login(self):
        """
        Tests sending of notifications for previously sent results but later
        change in locaion.
        """

        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='act',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')

    