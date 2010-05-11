import datetime
import time

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.locations.models import Location, LocationType

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.reminders.app import App
from mwana.apps.reminders import models as reminders
from mwana.apps.reminders import tasks
from mwana import const


class EventRegistration(TestScript):
    
    def _register(self):
        clinic = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        Location.objects.create(name="Kafue District Hospital", slug="kdh",
                                type=clinic)
        script = """
            kk     > agent kdh 01 rupiah banda
            kk     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 01 of Kafue District Hospital.
            kk     > agent kdh 01 rupiah banda
            kk     < Hello Rupiah Banda! You are already registered as a RemindMi Agent for zone 01 of Kafue District Hospital.
            """
        self.runScript(script)
    
    def testMalformedMessage(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth
            kk     < Sorry, I didn't understand that. To add a birth, send BIRTH <DATE> <NAME>. The date is optional and is logged as TODAY if left out.
            kk     > birth 24 3 2010
            kk     < Sorry, I didn't understand that. To add a birth, send BIRTH <DATE> <NAME>. The date is optional and is logged as TODAY if left out.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(0, patients.count())

    def testBadDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth 34553 maria
            kk     < Sorry, I couldn't understand that date. Please enter the date like so: DAY MONTH YEAR, for example: 23 04 2010
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(0, patients.count())

    def testEventRegistrationDateFormats(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth 4/3/2010 maria
            kk     < Thank you %(cba)s! You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4 3 2010 laura
            kk     < Thank you %(cba)s! You have successfully registered a birth for laura on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4-3-2010 anna
            kk     < Thank you %(cba)s! You have successfully registered a birth for anna on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4.3.2010 michelle
            kk     < Thank you %(cba)s! You have successfully registered a birth for michelle on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4. 3. 2010 anne
            kk     < Thank you %(cba)s! You have successfully registered a birth for anne on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 04032010 heidi
            kk     < Thank you %(cba)s! You have successfully registered a birth for heidi on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4/3 rachel
            kk     < Thank you %(cba)s! You have successfully registered a birth for rachel on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4 3 nancy
            kk     < Thank you %(cba)s! You have successfully registered a birth for nancy on 04/03/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4-3 katrina
            kk     < Thank you %(cba)s! You have successfully registered a birth for katrina on 04/03/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4.3 molly
            kk     < Thank you %(cba)s! You have successfully registered a birth for molly on 04/03/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4. 3 lisa
            kk     < Thank you %(cba)s! You have successfully registered a birth for lisa on 04/03/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 0403 lauren
            kk     < Thank you %(cba)s! You have successfully registered a birth for lauren on 04/03/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
        """ % {'year': datetime.datetime.now().year, 'cba': "Rupiah Banda"}
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(12, patients.count())
        for patient in patients:
            self.assertEqual(1, patient.patient_events.count())
            patient_event = patient.patient_events.get()
            self.assertEqual(patient_event.date, datetime.date(2010, 3, 4))
            self.assertEqual(patient_event.event.slug, "birth")

    def testCorrectMessageWithGender(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth", gender='f')
        script = """
            kk     > birth 4/3/2010 maria
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(1, patients.count())
        
    def testCorrectMessageWithoutRegisteringAgent(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            aa     > birth 4/3/2010 maria
            aa     < Thank you! You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(1, patients.count())

    def testCorrectMessageWithManyKeywords(self):
        self._register()
        reminders.Event.objects.create(name="Birth", gender="f",
                                       slug="birth|bith|bilth|mwana")
        script = """
            kk     > bIrth 4/3/2010 maria
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > bith 4/3/2010 anna
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for anna on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > BILTH 4/3/2010 laura
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for laura on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > mwaNA 4/3/2010 lynn
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for lynn on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > unknownevent 4/3/2010 lynn
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(4, patients.count())
        
    def testCorrectMessageWithoutDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth maria
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for maria on %s. You will be notified when it is time for his or her next appointment at the clinic.
        """ % datetime.date.today().strftime('%d/%m/%Y')
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(1, patients.count())
        patient = patients.get()
        self.assertEqual(1, patient.patient_events.count())
        patient_event = patient.patient_events.get()
        self.assertEqual(patient_event.date, datetime.date.today())
        self.assertEqual(patient_event.event.slug, "birth")

    def testDuplicateEventRegistration(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth", gender='f')
        script = """
            kk     > birth 4/3/2010 maria
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > birth 4/3/2010 maria
            kk     < Hello Rupiah Banda! I am sorry, but someone has already registered a birth for maria on 04/03/2010.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(1, patients.count())

    def testFutureEventRegistration(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth", gender='f')
        script = """
            kk     > birth 4/6/2010 maria
            kk     < Sorry, you can not register a birth with a date after today's.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(0, patients.count())

    
class Reminders(TestScript):

    apps = (handler_app, App,)
    
    def testSendReminders(self):
        birth = reminders.Event.objects.create(name="Birth", slug="birth",
                                               gender="f")
        birth.appointments.create(name='2 day', num_days=2)
        birth.appointments.create(name='3 day', num_days=3)
        birth.appointments.create(name='4 day', num_days=4)
        clinic = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        zone = const.get_zone_type()
        central = Location.objects.create(name='Central Clinic', type=clinic)
        zone1 = Location.objects.create(name='Zone 1', type=zone,
                                        parent=central, slug='zone1')
        zone2 = Location.objects.create(name='Zone 2', type=zone,
                                        parent=central, slug='zone2')
        patient1 = Contact.objects.create(name='patient 1', location=zone1)
        patient2 = Contact.objects.create(name='patient 2', location=zone1)
        patient3 = Contact.objects.create(name='patient 3', location=zone2)
        
        # this gets the backend and connection in the db
        self.runScript("""
        cba1 > hello world
        cba2 > hello world
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
        cba2_conn = Connection.objects.get(identity="cba2")
        cba2 = Contact.objects.create(name='cba2', location=zone2)
        cba2.types.add(cba_t)
        cba2_conn.contact = cba2
        cba2_conn.save()
        birth.patient_events.create(patient=patient1, cba_conn=cba1_conn,
                                    date=datetime.datetime.today())
        birth.patient_events.create(patient=patient2, cba_conn=cba1_conn,
                                    date=datetime.datetime.today())
        birth.patient_events.create(patient=patient3, cba_conn=cba2_conn,
                                    date=datetime.datetime.today())
        self.startRouter()
        tasks.send_notifications(self.router)
        # just the 1 and two day notifications should go out;
        # 3 patients x 2 notifications = 6 messages
        messages = self.receiveAllMessages()
        expected_messages =\
            ['Hello cba1. patient 1 is due for their next clinic appointment. '
             'Please deliver a reminder to this person and ensure they '
             'visit Central Clinic within 3 days.',
             'Hello cba1. patient 2 is due for their next clinic appointment. '
             'Please deliver a reminder to this person and ensure they '
             'visit Central Clinic within 3 days.',
             'Hello cba2. patient 3 is due for their next clinic appointment. '
             'Please deliver a reminder to this person and ensure they '
             'visit Central Clinic within 3 days.']
        self.assertEqual(len(messages), len(expected_messages))
        for msg in messages:
            self.assertTrue(msg.text in expected_messages, msg)
        sent_notifications = reminders.SentNotification.objects.all()
        self.assertEqual(sent_notifications.count(), len(expected_messages))
        
    def testRemindersSentOnlyOnce(self):
        """
        tests that notification messages are sent only sent once
        """
        birth = reminders.Event.objects.create(name="Birth", slug="birth")
        birth.appointments.create(name='1 day', num_days=2)
        patient1 = Contact.objects.create(name='patient 1')
        
        # this gets the backend and connection in the db
        self.runScript("""cba > hello world""")
        # take a break to allow the router thread to catch up; otherwise we
        # get some bogus messages when they're retrieved below
        time.sleep(.1)
        cba_conn = Connection.objects.get(identity="cba")
        birth.patient_events.create(patient=patient1, cba_conn=cba_conn,
                                    date=datetime.datetime.today())
        self.startRouter()
        tasks.send_notifications(self.router)
        # just the 1 and two day notifications should go out;
        # 3 patients x 2 notifications = 6 messages
        messages = self.receiveAllMessages()
        self.assertEqual(len(messages), 1)
        sent_notifications = reminders.SentNotification.objects.all()
        self.assertEqual(sent_notifications.count(), 1)

        # make sure no new messages go out if the method is called again
        tasks.send_notifications(self.router)
        messages = self.receiveAllMessages()
        self.assertEqual(len(messages), 0)
        sent_notifications = reminders.SentNotification.objects.all()
        # number of sent notifications should still be 1 (not 2)
        self.assertEqual(sent_notifications.count(), 1)
        
        self.stopRouter()
        
    def testRemindersNoLocation(self):
        birth = reminders.Event.objects.create(name="Birth", slug="birth")
        birth.appointments.create(name='1 day', num_days=2)
        patient1 = Contact.objects.create(name='Henry')
        
        # this gets the backend and connection in the db
        self.runScript("""cba > hello world""")
        # take a break to allow the router thread to catch up; otherwise we
        # get some bogus messages when they're retrieved below
        time.sleep(.1)
        cba_conn = Connection.objects.get(identity="cba")
        cba = Contact.objects.create(name='Rupiah Banda')
        cba_conn.contact = cba
        cba_conn.save()
        birth.patient_events.create(patient=patient1, cba_conn=cba_conn,
                                    date=datetime.datetime.today())
        self.startRouter()
        tasks.send_notifications(self.router)
        # just the 1 and two day notifications should go out;
        # 3 patients x 2 notifications = 6 messages
        messages = self.receiveAllMessages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text, "Hello Rupiah Banda. Henry is due "
                         "for their next clinic appointment. Please deliver a "
                         "reminder to this person and ensure they visit "
                         "the clinic within 3 days.")
        sent_notifications = reminders.SentNotification.objects.all()
        self.assertEqual(sent_notifications.count(), 1)
        
    def testRemindersRegistered(self):
        birth = reminders.Event.objects.create(name="Birth", slug="birth")
        birth.appointments.create(name='1 day', num_days=2)
        clinic = LocationType.objects.create(singular='Clinic',
                                             plural='Clinics', slug='clinic')
        central = Location.objects.create(name='Central Clinic', type=clinic)
        patient1 = Contact.objects.create(name='Henry', location=central)
        
        # this gets the backend and connection in the db
        self.runScript("""cba > hello world""")
        # take a break to allow the router thread to catch up; otherwise we
        # get some bogus messages when they're retrieved below
        time.sleep(.1)
        cba_conn = Connection.objects.get(identity="cba")
        cba = Contact.objects.create(name='cba', location=central)
        cba_type = ContactType.objects.create(name='CBA', slug='cba')
        cba.types.add(cba_type)
        cba_conn.contact = cba
        cba_conn.save()
        birth.patient_events.create(patient=patient1, cba_conn=cba_conn,
                                    date=datetime.datetime.today())
        self.startRouter()
        tasks.send_notifications(self.router)
        # just the 1 and two day notifications should go out;
        # 3 patients x 2 notifications = 6 messages
        messages = self.receiveAllMessages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text, "Hello cba. Henry is due for "
                         "their next clinic appointment. Please deliver a "
                         "reminder to this person and ensure they visit "
                         "Central Clinic within 3 days.")
        sent_notifications = reminders.SentNotification.objects.all()
        self.assertEqual(sent_notifications.count(), 1)
        
