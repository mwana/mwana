# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import LAB_TYPE
from mwana.apps.act.models import PHARMACY_TYPE
from mwana.apps.act.models import FlowCHWRegistration
from mwana.apps.act.models import ReminderMessagePreference
from mwana.apps.act.models import HistoricalEvent
from mwana.apps.act.models import SentReminder
from mwana.apps.act.models import ReminderDay
from mwana.apps.act.models import RemindersSwitch
from mwana.apps.act.models import Appointment
from mwana.apps.act.models import CHW
from mwana.apps.act import tasks
from django.conf import settings
import uuid
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
        self.clinic = Location.objects.create(type=self.type, name="Mibenge", slug="402029", parent=self.samfya,
                                              send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central", slug="403012",
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


class TestApp(ActSetUp):
    def create_chw(self, chw_con='chw', name='Donald Clinton'):
        script = """
            {chw} > blah blah 101010
            {chw} < Please send the keyword HELP if you need to be assisted.
        """.format(chw=chw_con)
        self.runScript(script)
        conn = Connection.objects.get(identity=chw_con)

        return CHW.objects.create(location=self.clinic, connection=conn, name=name, uuid=uuid.uuid1())

    def create_client(self, client_con='client', sex='m', community_worker=None):
        script = """
               {client} > blah blah 101010
               {client} < Please send the keyword HELP if you need to be assisted.
           """.format(client=client_con)
        self.runScript(script)
        client = Client(connection=Connection.objects.get(identity=client_con),
                        phone=client_con, sex=sex,
                        location=self.clinic, phone_verified=True, community_worker=community_worker)

        client.save()
        return client


    def testCHWRegistration(self):
        script = """
                chw > ACT CHW
                chw < Welcome to the ACT Program. To register as a CHW reply with your name.
                chw > Donald Clinton
                chw < Thank you Donald Clinton. Now reply with your NRC
                chw > 403012/12/1
                chw < Thank you Donald Clinton. Now reply with your clinic code
                chw > 403012
                chw < Donald Clinton you have successfully joined as CHW for the ACT Program from Central clinic and your NRC is 403012/12/1. If this is NOT correct send 4444 and register again
            """
        self.runScript(script)
        self.assertEqual(0, FlowCHWRegistration.objects.count())
        chw = CHW.objects.get(pk=1)
        self.assertEqual(chw.connection.identity, 'chw')
        self.assertEqual(chw.phone_verified, True)
        self.assertEqual(chw.phone, 'chw')
        self.assertEqual(chw.name, 'Donald Clinton')
        self.assertEqual(chw.is_active, True)
        self.assertEqual(chw.location, self.mansa_central)
        self.assertEqual(CHW.objects.all().count(), 1)


    def testCHWRegistrationErrorHandling(self):
        script = """
                chw > ACT CHW 101010 x8
                chw < Welcome to the ACT Program. To register as a CHW reply with your name.
                chw > Donald Clinton
                chw < Thank you Donald Clinton. Now reply with your NRC
                chw > okay
                chw < Sorry okay is not a valid NRC number. Reply with correct NRC number
                chw > 2222/2/2
                chw < Sorry 2222/2/2 is not a valid NRC number. Reply with correct NRC number
                chw > 12222/2/2
                chw < Sorry 12222/2/2 is not a valid NRC number. Reply with correct NRC number
                chw > 112222/2/2
                chw < Sorry 112222/2/2 is not a valid NRC number. Reply with correct NRC number
                chw > 112222/2/1
                chw < Thank you Donald Clinton. Now reply with your clinic code
                chw > okay
                chw < Sorry, I don't know about a clinic with code okay. Please check your code and try again.
                chw > zone
                chw < Sorry, I don't know about a clinic with code zone. Please check your code and try again.
                chw > 402029
                chw < Donald Clinton you have successfully joined as CHW for the ACT Program from Mibenge clinic and your NRC is 112222/2/1. If this is NOT correct send 4444 and register again
                chw > ACT CHW
                chw < Your phone is already registered to Donald Clinton of Mibenge health facility. Send HELP ACT if you need to be assisted
                chw > 4444
                chw < You have successfully unsubscribed Donald Clinton.
                chw > act CHW
                chw < Welcome to the ACT Program. To register as a CHW reply with your name.
                chw > Hillary Trump
                chw < Thank you Hillary Trump. Now reply with your NRC
                chw > 101010/12/1
                chw < Thank you Hillary Trump. Now reply with your clinic code
                chw > 403012
                chw < Hillary Trump you have successfully joined as CHW for the ACT Program from Central clinic and your NRC is 101010/12/1. If this is NOT correct send 4444 and register again
            """
        self.runScript(script)
        self.assertEqual(0, FlowCHWRegistration.objects.count())
        chw = CHW.objects.get(pk=1)
        self.assertEqual(chw.connection.identity, 'chw')
        self.assertEqual(chw.name, 'Donald Clinton')
        self.assertEqual(chw.is_active, False)
        self.assertEqual(chw.location, self.clinic)
        chw = CHW.objects.get(pk=2)
        self.assertEqual(chw.connection.identity, 'chw')
        self.assertEqual(chw.name, 'Hillary Trump')
        self.assertEqual(chw.is_active, True)
        self.assertEqual(chw.location, self.mansa_central)
        self.assertEqual(CHW.objects.all().count(), 2)


    def testClientRegistrationByUnknownUser(self):
        script = """
                +260979112233 > ACT CLIENT
                +260979112233 < Sorry, you must be registered as a CHW for the ACT Program before you can register a client. Reply with HELP ACT if you need to be assisted
                """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 0)
        # TODO: test re-registration


    def testClientRegistration(self):
        chw = self.create_chw(chw_con='+260979112233')
        script = """
                +260979112233 > ACT CHILD
                +260979112233 < Hi Donald Clinton, to register a client first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < You have submitted client's ID 403012-12-1. Now reply with the client's name
                +260979112233 > Robert mukale
                +260979112233 < You have submitted client's name as Robert Mukale. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006
                +260979112233 > 12 02 2008
                +260979112233 < You have submitted client's date of birth as 12 Feb 2008. Now reply with the client's gender, F for Female or M if Male
                +260979112233 > f
                +260979112233 < You have submitted client's gender as Female. Will client be receiving SMS messages, Reply with Y for Yes or N for No?
                +260979112233 > N
                +260979112233 < Thank you Donald Clinton. Now reply with the client's phone number or N/A if client or caregiver does not have a phone
                +260979112233 > 0977123456
                +260979112233 < Client's name is Robert Mukale, ID is 403012-12-1, DOB is 12 February 2008, gender is Female, phone # is +260977123456, will receive SMS: No. Reply with Yes if this is correct or No if not
                +260979112233 > Yes
                +260979112233 < Thank you Donald Clinton. You have successfully registered the client Robert Mukale
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.national_id, '403012-12-1')
        self.assertEqual(settings.GET_ORIGINAL_TEXT(client.name), 'Robert Mukale')
        self.assertEqual(client.community_worker, chw)
        self.assertEqual(client.dob.year, 2008)
        self.assertEqual(client.dob.month, 2)
        self.assertEqual(client.dob.day, 12)
        self.assertEqual(client.sex, 'f')
        self.assertEqual(client.can_receive_messages, False)
        self.assertEqual(client.location, self.clinic)
        self.assertEqual(client.phone, '+260977123456')
        self.assertEqual(client.phone_verified, False)
        self.assertEqual(client.connection, None)
        self.assertEqual(client.alias, 'RM-403012-12-1')


    def testClientRegistrationNoPhone(self):
        chw = self.create_chw(chw_con='+260979112233')
        script = """
                +260979112233 > ACT CHILD
                +260979112233 < Hi Donald Clinton, to register a client first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < You have submitted client's ID 403012-12-1. Now reply with the client's name
                +260979112233 > Robert mukale
                +260979112233 < You have submitted client's name as Robert Mukale. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006
                +260979112233 > 12 02 2008
                +260979112233 < You have submitted client's date of birth as 12 Feb 2008. Now reply with the client's gender, F for Female or M if Male
                +260979112233 > f
                +260979112233 < You have submitted client's gender as Female. Will client be receiving SMS messages, Reply with Y for Yes or N for No?
                +260979112233 > N
                +260979112233 < Thank you Donald Clinton. Now reply with the client's phone number or N/A if client or caregiver does not have a phone
                +260979112233 > N/A
                +260979112233 < Client's name is Robert Mukale, ID is 403012-12-1, DOB is 12 February 2008, gender is Female. Reply with Yes if this is correct or No if not
                +260979112233 > Yes
                +260979112233 < Thank you Donald Clinton. You have successfully registered the client Robert Mukale
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        self.assertEqual(FlowCHWRegistration.objects.all().count(), 0)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.national_id, '403012-12-1')
        self.assertEqual(settings.GET_ORIGINAL_TEXT(client.name), 'Robert Mukale')
        self.assertEqual(client.community_worker, chw)
        self.assertEqual(client.dob.year, 2008)
        self.assertEqual(client.dob.month, 2)
        self.assertEqual(client.dob.day, 12)
        self.assertEqual(client.sex, 'f')
        self.assertEqual(client.can_receive_messages, False)
        self.assertEqual(client.location, self.clinic)
        self.assertEqual(client.phone, None)
        self.assertEqual(client.phone_verified, False)
        self.assertEqual(client.connection, None)
        self.assertEqual(client.alias, 'RM-403012-12-1')


    def testClientRegistrationMaleSMSYes(self):
        chw = self.create_chw(chw_con='+260979112233')
        script = """
                +260979112233 > ACT CHILD
                +260979112233 < Hi Donald Clinton, to register a client first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < You have submitted client's ID 403012-12-1. Now reply with the client's name
                +260979112233 > Robert mukale
                +260979112233 < You have submitted client's name as Robert Mukale. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006
                +260979112233 > 12 02 2008
                +260979112233 < You have submitted client's date of birth as 12 Feb 2008. Now reply with the client's gender, F for Female or M if Male
                +260979112233 > m
                +260979112233 < You have submitted client's gender as Male. Will client be receiving SMS messages, Reply with Y for Yes or N for No?
                +260979112233 > y
                +260979112233 < Thank you Donald Clinton. Now reply with the client's phone number or N/A if client or caregiver does not have a phone
                +260979112233 > 0977123456
                +260979112233 < Client's name is Robert Mukale, ID is 403012-12-1, DOB is 12 February 2008, gender is Male, phone # is +260977123456, will receive SMS: Yes. Reply with Yes if this is correct or No if not
                +260979112233 > Yes
                +260979112233 < Thank you Donald Clinton. You have successfully registered the client Robert Mukale
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.national_id, '403012-12-1')
        self.assertEqual(settings.GET_ORIGINAL_TEXT(client.name), 'Robert Mukale')
        self.assertEqual(client.community_worker, chw)
        self.assertEqual(client.dob.year, 2008)
        self.assertEqual(client.dob.month, 2)
        self.assertEqual(client.dob.day, 12)
        self.assertEqual(client.sex, 'm')
        self.assertEqual(client.can_receive_messages, True)
        self.assertEqual(client.location, self.clinic)
        self.assertEqual(client.phone, '+260977123456')
        self.assertEqual(client.phone_verified, False)
        self.assertEqual(client.connection, None)
        self.assertEqual(client.alias, 'RM-403012-12-1')


    def testClientRegistrationCanceled(self):
        chw = self.create_chw(chw_con='+260979112233')
        script = """
                +260979112233 > ACT CLIENT
                +260979112233 < Hi Donald Clinton, to register a client first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < You have submitted client's ID 403012-12-1. Now reply with the client's name
                +260979112233 > Robert mukale
                +260979112233 < You have submitted client's name as Robert Mukale. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006
                +260979112233 > 12 02 2008
                +260979112233 < You have submitted client's date of birth as 12 Feb 2008. Now reply with the client's gender, F for Female or M if Male
                +260979112233 > m
                +260979112233 < You have submitted client's gender as Male. Will client be receiving SMS messages, Reply with Y for Yes or N for No?
                +260979112233 > y
                +260979112233 < Thank you Donald Clinton. Now reply with the client's phone number or N/A if client or caregiver does not have a phone
                +260979112233 > 0977123456
                +260979112233 < Client's name is Robert Mukale, ID is 403012-12-1, DOB is 12 February 2008, gender is Male, phone # is +260977123456, will receive SMS: Yes. Reply with Yes if this is correct or No if not
                +260979112233 > No
                +260979112233 < You can start a new submission by sending ACT CLIENT or ACT CHILD
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 0)
        self.assertEqual(FlowCHWRegistration.objects.all().count(), 0)


    def testClientRegistrationErrorHandling(self):
        chw = self.create_chw(chw_con='+260979112233')
        script = """
                +260979112233 > ACT PATIENT
                +260979112233 < Hi Donald Clinton, to register a client first reply with client's unique ID
                +260979112233 > 403012
                +260979112233 < Sorry 403012 is not a valid unique ID. Reply with correct unique ID.
                +260979112233 > 403012-12-1
                +260979112233 < You have submitted client's ID 403012-12-1. Now reply with the client's name
                +260979112233 > Rob
                +260979112233 < Rob does not look like a valid name. Reply with a valid name
                +260979112233 > Robert mukale
                +260979112233 < You have submitted client's name as Robert Mukale. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006
                +260979112233 > 12 02 08
                +260979112233 < Date 12 02 08 has an invalid year. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997.
                +260979112233 >  x 2008
                +260979112233 < x 2008 does not look like a valid date. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997.
                +260979112233 >  13 2008
                +260979112233 < 13 2008 does not look like a valid date. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997.
                +260979112233 > 12 13 2008
                +260979112233 < Date 12 13 2008 has an invalid month. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997.
                +260979112233 > 12 02 2028
                +260979112233 < Sorry, client's date of birth 12 02 2028 is after today's. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997.
                +260979112233 > 40 02 2008
                +260979112233 < 40 02 2008 does not look like a valid date. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997.
                +260979112233 > 12 02 2008
                +260979112233 < You have submitted client's date of birth as 12 Feb 2008. Now reply with the client's gender, F for Female or M if Male
                +260979112233 > man
                +260979112233 < Sorry, client's gender must be F or M. Reply with the client's gender, F for Female or M if Male
                +260979112233 > c
                +260979112233 < Sorry, client's gender must be F or M. Reply with the client's gender, F for Female or M if Male
                +260979112233 > boy
                +260979112233 < Sorry, client's gender must be F or M. Reply with the client's gender, F for Female or M if Male
                +260979112233 > men
                +260979112233 < Sorry, client's gender must be F or M. Reply with the client's gender, F for Female or M if Male
                +260979112233 > Male
                +260979112233 < You have submitted client's gender as Male. Will client be receiving SMS messages, Reply with Y for Yes or N for No?
                +260979112233 > yo
                +260979112233 < Sorry, I din't understand that. Reply with Y if client will be receiving SMS messages or N if not
                +260979112233 > yep
                +260979112233 < Sorry, I din't understand that. Reply with Y if client will be receiving SMS messages or N if not
                +260979112233 > y
                +260979112233 < Thank you Donald Clinton. Now reply with the client's phone number or N/A if client or caregiver does not have a phone
                +260979112233 >
                +260979112233 < Sorry, I couldn't read your message. Make sure you have correct GSM message settings on your phone
                +260979112233 > 077123456
                +260979112233 < Sorry 077123456 is not a valid Airtel or MTN number. Reply with correct number
                +260979112233 > 0777123456
                +260979112233 < Sorry 0777123456 is not a valid Airtel or MTN number. Reply with correct number
                +260979112233 > 09777123456
                +260979112233 < Sorry 09777123456 is not a valid Airtel or MTN number. Reply with correct number
                +260979112233 > 0977123456
                +260979112233 < Client's name is Robert Mukale, ID is 403012-12-1, DOB is 12 February 2008, gender is Male, phone # is +260977123456, will receive SMS: Yes. Reply with Yes if this is correct or No if not
                +260979112233 > whatever
                +260979112233 < Client's name is Robert Mukale, ID is 403012-12-1, DOB is 12 February 2008, gender is Male, phone # is +260977123456, will receive SMS: Yes. Reply with Yes if this is correct or No if not
                +260979112233 > Yes
                +260979112233 < Thank you Donald Clinton. You have successfully registered the client Robert Mukale
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.national_id, '403012-12-1')
        self.assertEqual(settings.GET_ORIGINAL_TEXT(client.name), 'Robert Mukale')
        self.assertEqual(client.community_worker, chw)
        self.assertEqual(client.dob.year, 2008)
        self.assertEqual(client.dob.month, 2)
        self.assertEqual(client.dob.day, 12)
        self.assertEqual(client.sex, 'm')
        self.assertEqual(client.can_receive_messages, True)
        self.assertEqual(client.location, self.clinic)
        self.assertEqual(client.phone, '+260977123456')
        self.assertEqual(client.phone_verified, False)
        self.assertEqual(client.connection, None)
        self.assertEqual(client.alias, 'RM-403012-12-1')


    def testClientReRegistration(self):
        chw = self.create_chw(chw_con='+260979112233')
        script = """
                +260979112233 > ACT CHILD
                +260979112233 < Hi Donald Clinton, to register a client first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < You have submitted client's ID 403012-12-1. Now reply with the client's name
                +260979112233 > Robert mukale
                +260979112233 < You have submitted client's name as Robert Mukale. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006
                +260979112233 > 12 02 2008
                +260979112233 < You have submitted client's date of birth as 12 Feb 2008. Now reply with the client's gender, F for Female or M if Male
                +260979112233 > f
                +260979112233 < You have submitted client's gender as Female. Will client be receiving SMS messages, Reply with Y for Yes or N for No?
                +260979112233 > N
                +260979112233 < Thank you Donald Clinton. Now reply with the client's phone number or N/A if client or caregiver does not have a phone
                +260979112233 > 0977123456
                +260979112233 < Client's name is Robert Mukale, ID is 403012-12-1, DOB is 12 February 2008, gender is Female, phone # is +260977123456, will receive SMS: No. Reply with Yes if this is correct or No if not
                +260979112233 > Yes
                +260979112233 < Thank you Donald Clinton. You have successfully registered the client Robert Mukale
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.national_id, '403012-12-1')
        self.assertEqual(client.alias, 'RM-403012-12-1')
        self.assertEqual(settings.GET_ORIGINAL_TEXT(client.name), 'Robert Mukale')
        self.assertEqual(client.community_worker, chw)
        self.assertEqual(client.dob.year, 2008)
        self.assertEqual(client.dob.month, 2)
        self.assertEqual(client.dob.day, 12)
        self.assertEqual(client.sex, 'f')
        self.assertEqual(client.can_receive_messages, False)
        self.assertEqual(client.location, self.clinic)
        self.assertEqual(client.phone, '+260977123456')
        self.assertEqual(client.phone_verified, False)
        self.assertEqual(client.connection, None)
        self.assertEqual(client.alias, 'RM-403012-12-1')

        script = """
                +260979112233 > ACT CHILD
                +260979112233 < Hi Donald Clinton, to register a client first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < A client, Robert Mukale, with ID 403012-12-1 already exists. Reply with correct ID or send HELP CLIENT if you need to be assisted
                +260979112233 > whatever
                +260979112233 < Sorry whatever is not a valid unique ID. Reply with correct unique ID.
                +260979112233 > 403012-12-2
                +260979112233 < You have submitted client's ID 403012-12-2. Now reply with the client's name
                +260979112233 > Grace mukale
                +260979112233 < You have submitted client's name as Grace Mukale. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006
                +260979112233 > 12 03 2008
                +260979112233 < You have submitted client's date of birth as 12 Mar 2008. Now reply with the client's gender, F for Female or M if Male
                +260979112233 > f
                +260979112233 < You have submitted client's gender as Female. Will client be receiving SMS messages, Reply with Y for Yes or N for No?
                +260979112233 > N
                +260979112233 < Thank you Donald Clinton. Now reply with the client's phone number or N/A if client or caregiver does not have a phone
                +260979112233 > 0977123456
                +260979112233 < Client's name is Grace Mukale, ID is 403012-12-2, DOB is 12 March 2008, gender is Female, phone # is +260977123456, will receive SMS: No. Reply with Yes if this is correct or No if not
                +260979112233 > Yes
                +260979112233 < Thank you Donald Clinton. You have successfully registered the client Grace Mukale
            """
        self.runScript(script)

    def testLabAppointmentRegistration(self):
        chw = self.create_chw(chw_con='+260979112233')
        client = self.create_client(client_con='+260979676767')
        client.national_id = '805010-12345-1'
        client.name = settings.GET_CLEANED_TEXT('Rebekah Malope')
        client.save()
        script = """
                +260979112233 > ACT visit
                +260979112233 < Hi Donald Clinton, to register a client's appointment first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < Client with ID 403012-12-1 does not exist. Please verify the ID or to regsiter a new client send ACT CHILD
                +260979112233 > 805010-12345-1
                +260979112233 < ID 805010-12345-1 is for Rebekah Malope. Now reply with the appointment date like <DAY> <MONTH> <YEAR> e.g. 12 04 2018 for 12 April 2018.
                +260979112233 > 12 02 2018
                +260979112233 < You have submitted appointment date as 12 Feb 2018. Now reply with the type of appointment, L for Lab visit or P if Pharmacy visit
                +260979112233 > l
                +260979112233 < Now submit the client's preferred message type for Lab Visit. Refer to Job Aid on Message Preferences, e.g. m1 or m2 or m3 etc
                +260979112233 > m2
                +260979112233 < You have submitted Lab Visit appointment for Rebekah Malope for 12 February 2018. Reply with Yes if this is correct or No if not
                +260979112233 > Y
                +260979112233 < Thank you Donald Clinton. You have successfully registered a Lab Visit appointment for Rebekah Malope on 12 February 2018
                """
        self.runScript(script)
        pref = ReminderMessagePreference.objects.get(client=client)
        # @type pref ReminderMessagePreference
        self.assertEqual(pref.visit_type, LAB_TYPE)
        self.assertEqual(pref.get_message_id_display(), 'Good day. Happy day %(date)s')
        appointment  = Appointment.objects.get(pk=1)
        self.assertEqual(appointment.client, client)
        self.assertEqual(appointment.type, LAB_TYPE)
        self.assertEqual(appointment.date, date(2018, 2, 12))
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.cha_responsible, chw)

    def testPharmacyAppointmentRegistration(self):
        chw = self.create_chw(chw_con='+260979112233')
        client = self.create_client(client_con='+260979676767')
        client.national_id = '805010-12345-1'
        client.name = settings.GET_CLEANED_TEXT('Rebekah Malope')
        client.save()
        script = """
                +260979112233 > ACT visit
                +260979112233 < Hi Donald Clinton, to register a client's appointment first reply with client's unique ID
                +260979112233 > 805010-12345-1
                +260979112233 < ID 805010-12345-1 is for Rebekah Malope. Now reply with the appointment date like <DAY> <MONTH> <YEAR> e.g. 12 04 2018 for 12 April 2018.
                +260979112233 > 1 01 2018
                +260979112233 < You have submitted appointment date as 01 Jan 2018. Now reply with the type of appointment, L for Lab visit or P if Pharmacy visit
                +260979112233 > p
                +260979112233 < Now submit the client's preferred message type for Pharmacy Visit. Refer to Job Aid on Message Preferences, e.g. m1 or m2 or m3 etc
                +260979112233 > m1
                +260979112233 < You have submitted Pharmacy Visit appointment for Rebekah Malope for 01 January 2018. Reply with Yes if this is correct or No if not
                +260979112233 > Y
                +260979112233 < Thank you Donald Clinton. You have successfully registered a Pharmacy Visit appointment for Rebekah Malope on 01 January 2018
                """
        self.runScript(script)
        pref = ReminderMessagePreference.objects.get(client=client)
        # @type pref ReminderMessagePreference
        self.assertEqual(pref.visit_type, PHARMACY_TYPE)
        self.assertEqual(pref.get_message_id_display(), 'Happy health day %(date)s')
        appointment  = Appointment.objects.get(pk=1)
        self.assertEqual(appointment.client, client)
        self.assertEqual(appointment.type, PHARMACY_TYPE)
        self.assertEqual(appointment.date, date(2018, 1, 1))
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.cha_responsible, chw)


    def testSuccessiveDifferentTypeAppointmentRegistrations(self):
        chw = self.create_chw(chw_con='+260979112233')
        client = self.create_client(client_con='+260979676767')
        client.national_id = '805010-12345-1'
        client.name = settings.GET_CLEANED_TEXT('Rebekah Malope')
        client.save()
        script = """
                +260979112233 > ACT visit
                +260979112233 < Hi Donald Clinton, to register a client's appointment first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < Client with ID 403012-12-1 does not exist. Please verify the ID or to regsiter a new client send ACT CHILD
                +260979112233 > 805010-12345-1
                +260979112233 < ID 805010-12345-1 is for Rebekah Malope. Now reply with the appointment date like <DAY> <MONTH> <YEAR> e.g. 12 04 2018 for 12 April 2018.
                +260979112233 > 12 02 2018
                +260979112233 < You have submitted appointment date as 12 Feb 2018. Now reply with the type of appointment, L for Lab visit or P if Pharmacy visit
                +260979112233 > l
                +260979112233 < Now submit the client's preferred message type for Lab Visit. Refer to Job Aid on Message Preferences, e.g. m1 or m2 or m3 etc
                +260979112233 > m2
                +260979112233 < You have submitted Lab Visit appointment for Rebekah Malope for 12 February 2018. Reply with Yes if this is correct or No if not
                +260979112233 > Y
                +260979112233 < Thank you Donald Clinton. You have successfully registered a Lab Visit appointment for Rebekah Malope on 12 February 2018
                """
        self.runScript(script)
        pref = ReminderMessagePreference.objects.get(client=client)
        # @type pref ReminderMessagePreference
        self.assertEqual(pref.visit_type, LAB_TYPE)
        self.assertEqual(pref.get_message_id_display(), 'Good day. Happy day %(date)s')
        appointment  = Appointment.objects.get(pk=1)
        self.assertEqual(appointment.client, client)
        self.assertEqual(appointment.type, LAB_TYPE)
        self.assertEqual(appointment.date, date(2018, 2, 12))
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.cha_responsible, chw)

    
        script = """
                +260979112233 > ACT visit
                +260979112233 < Hi Donald Clinton, to register a client's appointment first reply with client's unique ID
                +260979112233 > 805010-12345-1
                +260979112233 < ID 805010-12345-1 is for Rebekah Malope. Now reply with the appointment date like <DAY> <MONTH> <YEAR> e.g. 12 04 2018 for 12 April 2018.
                +260979112233 > 1 01 2018
                +260979112233 < You have submitted appointment date as 01 Jan 2018. Now reply with the type of appointment, L for Lab visit or P if Pharmacy visit
                +260979112233 > p
                +260979112233 < Now submit the client's preferred message type for Pharmacy Visit. Refer to Job Aid on Message Preferences, e.g. m1 or m2 or m3 etc
                +260979112233 > m1
                +260979112233 < You have submitted Pharmacy Visit appointment for Rebekah Malope for 01 January 2018. Reply with Yes if this is correct or No if not
                +260979112233 > Y
                +260979112233 < Thank you Donald Clinton. You have successfully registered a Pharmacy Visit appointment for Rebekah Malope on 01 January 2018
                """
        self.runScript(script)
        pref = ReminderMessagePreference.objects.get(client=client, pk=2)
        # @type pref ReminderMessagePreference
        self.assertEqual(pref.visit_type, PHARMACY_TYPE)
        self.assertEqual(pref.get_message_id_display(), 'Happy health day %(date)s')
        appointment  = Appointment.objects.get(pk=2)
        self.assertEqual(appointment.client, client)
        self.assertEqual(appointment.type, PHARMACY_TYPE)
        self.assertEqual(appointment.date, date(2018, 1, 1))
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.cha_responsible, chw)

    def testSuccessiveSameTypeAppointmentRegistrations(self):
        chw = self.create_chw(chw_con='+260979112233')
        client = self.create_client(client_con='+260979676767')
        client.national_id = '805010-12345-1'
        client.name = settings.GET_CLEANED_TEXT('Rebekah Malope')
        client.save()
        script = """
                +260979112233 > ACT visit
                +260979112233 < Hi Donald Clinton, to register a client's appointment first reply with client's unique ID
                +260979112233 > 403012-12-1
                +260979112233 < Client with ID 403012-12-1 does not exist. Please verify the ID or to regsiter a new client send ACT CHILD
                +260979112233 > 805010-12345-1
                +260979112233 < ID 805010-12345-1 is for Rebekah Malope. Now reply with the appointment date like <DAY> <MONTH> <YEAR> e.g. 12 04 2018 for 12 April 2018.
                +260979112233 > 12 02 2018
                +260979112233 < You have submitted appointment date as 12 Feb 2018. Now reply with the type of appointment, L for Lab visit or P if Pharmacy visit
                +260979112233 > l
                +260979112233 < Now submit the client's preferred message type for Lab Visit. Refer to Job Aid on Message Preferences, e.g. m1 or m2 or m3 etc
                +260979112233 > m2
                +260979112233 < You have submitted Lab Visit appointment for Rebekah Malope for 12 February 2018. Reply with Yes if this is correct or No if not
                +260979112233 > Y
                +260979112233 < Thank you Donald Clinton. You have successfully registered a Lab Visit appointment for Rebekah Malope on 12 February 2018
                """
        self.runScript(script)
        pref = ReminderMessagePreference.objects.get(client=client)
        # @type pref ReminderMessagePreference
        self.assertEqual(pref.visit_type, LAB_TYPE)
        self.assertEqual(pref.get_message_id_display(), 'Good day. Happy day %(date)s')
        appointment  = Appointment.objects.get(pk=1)
        self.assertEqual(appointment.client, client)
        self.assertEqual(appointment.type, LAB_TYPE)
        self.assertEqual(appointment.date, date(2018, 2, 12))
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.cha_responsible, chw)


        script = """
                +260979112233 > ACT visit
                +260979112233 < Hi Donald Clinton, to register a client's appointment first reply with client's unique ID
                +260979112233 > 805010-12345-1
                +260979112233 < ID 805010-12345-1 is for Rebekah Malope. Now reply with the appointment date like <DAY> <MONTH> <YEAR> e.g. 12 04 2018 for 12 April 2018.
                +260979112233 > 1 01 2018
                +260979112233 < You have submitted appointment date as 01 Jan 2018. Now reply with the type of appointment, L for Lab visit or P if Pharmacy visit
                +260979112233 > l
                +260979112233 < You have submitted Lab Visit appointment for Rebekah Malope for 01 January 2018. Reply with Yes if this is correct or No if not
                +260979112233 > Y
                +260979112233 < Thank you Donald Clinton. You have successfully registered a Lab Visit appointment for Rebekah Malope on 01 January 2018
                """
        self.runScript(script)
        pref = ReminderMessagePreference.objects.get(pk=1)
        # @type pref ReminderMessagePreference
        self.assertEqual(ReminderMessagePreference.objects.count(), 1)
        self.assertEqual(pref.visit_type, LAB_TYPE)
        self.assertEqual(pref.get_message_id_display(), 'Good day. Happy day %(date)s')
        appointment  = Appointment.objects.get(pk=2)
        self.assertEqual(appointment.client, client)
        self.assertEqual(appointment.type, LAB_TYPE)
        self.assertEqual(appointment.date, date(2018, 1, 1))
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.cha_responsible, chw)
