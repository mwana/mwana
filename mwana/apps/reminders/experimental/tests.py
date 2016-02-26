# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.reminders.experimental.models import SentNotificationToClinic
from datetime import date
from datetime import timedelta
from random import randint
import time

from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.reminders import models as reminders
from mwana.apps.reminders.experimental.models import Supported
from mwana.apps.reminders.experimental.tasks import send_notifications_to_clinic
from rapidsms.models import Connection
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript


class MockReminders(TestScript):

    def setUp(self):
        # this call is required if you want to override setUp
        super(MockReminders, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="400000")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="403000", parent=self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="402000", parent=self.luapula)
        self.mibenge = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="403029", parent=self.mansa, send_live_results=True)
        self.kashitu = Location.objects.create(type=self.type, name="Kashitu Clinic", slug="402026", parent=self.samfya, send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent=self.mansa, send_live_results=True)
        
    

    def testSendNotificationsToClinic(self):
        birth = reminders.Event.objects.create(name="Birth", slug="birth",
                                               gender="f")
        birth.appointments.create(name='6 day', num_days=6)
        birth.appointments.create(name='6 week', num_days=42)
        birth.appointments.create(name='6 month', num_days=183)
        clinic = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        zone = LocationType.objects.create(slug=const.ZONE_SLUGS[0])
        central = Location.objects.create(name='Central Clinic', type=clinic)
        zone1 = Location.objects.create(name='Zone 1', type=zone,
                                        parent=central, slug='zone1')
        zone2 = Location.objects.create(name='Zone 2', type=zone,
                                        parent=central, slug='zone2')
        patient1 = Contact.objects.create(name='patient 1', location=zone1)
        patient2 = Contact.objects.create(name='patient 2', location=zone1)
        patient3 = Contact.objects.create(name='patient 3', location=zone2)
        patient4 = Contact.objects.create(name='patient 4', location=zone2)
        patient5 = Contact.objects.create(name='patient 5', location=zone2)

        # this gets the backend and connection in the db
        self.runScript("""
        cba1 > hello world
        staff > hello world
        staff2 > hello world
        """)
        # take a break to allow the router thread to catch up; otherwise we
        # get some bogus messages when they're retrieved below
        time.sleep(.1)
        cba_t = const.get_cba_type()
        cba1_conn = Connection.objects.get(identity="cba1")
        cba1 = Contact.objects.create(name='cba1', location=zone1)
        cba1.types.add(cba_t)
        cba1_conn.contact = cba1
        cba1_conn.save()



        staff_conn = Connection.objects.get(identity="staff")
        staff = Contact.objects.create(name='Suarez', location=central)
        staff.types.add(const.get_clinic_worker_type())
        staff_conn.contact = staff
        staff_conn.save()

        staff_conn2 = Connection.objects.get(identity="staff2")
        staff2 = Contact.objects.create(name='Robben', location=central)
        staff2.types.add(const.get_clinic_worker_type())
        staff_conn2.contact = staff2
        staff_conn2.save()

        today = date.today()
        # any random day this week
        this_week = today - timedelta(today.weekday() + randint(-5, 1))
        
        birth.patient_events.create(patient=patient1, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=6))
        birth.patient_events.create(patient=patient2, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=42))
        birth.patient_events.create(patient=patient3, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=42))
        birth.patient_events.create(patient=patient4, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=42))
        birth.patient_events.create(patient=patient5, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=183))

        Supported.objects.create(location=central, supported=True)
        self.startRouter()
        send_notifications_to_clinic(self.router)
        messages = self.receiveAllMessages()
        expected_messages = \
            ["Hello Suarez, 5 mothers are due for their clinic visits this week"
             ", 1 for 6 day clinic visit, 3 for 6 week clinic visit and 1 for 6"
             " month clinic visit.",
             "Hello Robben, 5 mothers are due for their clinic visits this week"
             ", 1 for 6 day clinic visit, 3 for 6 week clinic visit and 1 for 6"
             " month clinic visit."]
        self.assertEqual(len(messages), len(expected_messages))
        for msg in messages:
            self.assertTrue(msg.text in expected_messages, "'%s' is not in expected messages" % msg.text)

        sent_notifications = SentNotificationToClinic.objects.all()
        self.assertEqual(sent_notifications.count(), 4)# 1 four each appointment type for each clinic, + 1 for total
        self.assertEqual(sent_notifications.filter(recipients=2).count(), 4)
        self.assertEqual(sent_notifications.filter(event_name='6 day', number=1).count(), 1)
        self.assertEqual(sent_notifications.filter(event_name='6 week', number=3).count(), 1)
        self.assertEqual(sent_notifications.filter(event_name='6 month', number=1).count(), 1)

        #Only send once
        send_notifications_to_clinic(self.router)
        messages = self.receiveAllMessages()
        self.assertEqual(0, len(messages))

        # Test message for 1 mother with 6 day visit
        PatientEvent.objects.all().delete()
        SentNotificationToClinic.objects.all().delete()
        self.assertEqual(0, PatientEvent.objects.all().count())

        birth.patient_events.create(patient=patient1, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=6))


        send_notifications_to_clinic(self.router)
        messages = self.receiveAllMessages()
        expected_messages = \
            ["Hello Suarez, 1 mother is due for her 6 day clinic visit this week."
            ,"Hello Robben, 1 mother is due for her 6 day clinic visit this week."
             ]
        self.assertEqual(len(messages), len(expected_messages))
        for msg in messages:
            self.assertTrue(msg.text in expected_messages, "'%s' is not in expected messages" % msg.text)

        sent_notifications = SentNotificationToClinic.objects.all()
        self.assertEqual(sent_notifications.count(), 2)# 1 four each appointment type for each clinic, + 1 for total


        # Test message for 1 mother with 6 week visit
        PatientEvent.objects.all().delete()
        SentNotificationToClinic.objects.all().delete()
        self.assertEqual(0, PatientEvent.objects.all().count())

        birth.patient_events.create(patient=patient1, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=42))


        send_notifications_to_clinic(self.router)
        messages = self.receiveAllMessages()
        expected_messages = \
            ["Hello Suarez, 1 mother is due for her 6 week clinic visit this week."
            ,"Hello Robben, 1 mother is due for her 6 week clinic visit this week."
             ]
        self.assertEqual(len(messages), len(expected_messages))
        for msg in messages:
            self.assertTrue(msg.text in expected_messages, "'%s' is not in expected messages" % msg.text)

        sent_notifications = SentNotificationToClinic.objects.all()
        self.assertEqual(sent_notifications.count(), 2)# 1 four each appointment type for each clinic, + 1 for total

        # Test message for 1 mother with 6 month visit
        PatientEvent.objects.all().delete()
        SentNotificationToClinic.objects.all().delete()
        self.assertEqual(0, PatientEvent.objects.all().count())

        birth.patient_events.create(patient=patient1, cba_conn=cba1_conn,
                                    date=this_week - timedelta(days=183))


        send_notifications_to_clinic(self.router)
        messages = self.receiveAllMessages()
        expected_messages = \
            ["Hello Suarez, 1 mother is due for her 6 month clinic visit this week."
            ,"Hello Robben, 1 mother is due for her 6 month clinic visit this week."
             ]
        self.assertEqual(len(messages), len(expected_messages))
        for msg in messages:
            self.assertTrue(msg.text in expected_messages, "'%s' is not in expected messages" % msg.text)

        sent_notifications = SentNotificationToClinic.objects.all()
        self.assertEqual(sent_notifications.count(), 2)# 1 four each appointment type for each clinic, + 1 for total

        self.stopRouter()
