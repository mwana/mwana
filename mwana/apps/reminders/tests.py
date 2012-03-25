# vim: ai ts=4 sts=4 et sw=4
import datetime
import time

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from mwana.apps.locations.models import Location, LocationType

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.reminders.app import App
from mwana.apps.reminders import models as reminders
from mwana.apps.reminders import tasks
from mwana import const


class EventRegistration(TestScript):
    
#    "Hi %(cba)s.%(patient)s is due for %(type)s clinic visit.Please remind them to visit %(clinic)s within 3 days then reply with TOLD %(patient)s"
    
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
            kk     > birth 1/1/2012 maria
            kk     < Thank you %(cba)s! You have successfully registered a birth for maria on 01/01/2012. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1 1 2012 laura
            kk     < Thank you %(cba)s! You have successfully registered a birth for laura on 01/01/2012. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1-1-2012 anna
            kk     < Thank you %(cba)s! You have successfully registered a birth for anna on 01/01/2012. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1.1.2012 michelle
            kk     < Thank you %(cba)s! You have successfully registered a birth for michelle on 01/01/2012. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1. 1. 2012 anne
            kk     < Thank you %(cba)s! You have successfully registered a birth for anne on 01/01/2012. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 01012012 heidi
            kk     < Thank you %(cba)s! You have successfully registered a birth for heidi on 01/01/2012. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1/1 rachel
            kk     < Thank you %(cba)s! You have successfully registered a birth for rachel on 01/01/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1 1 nancy
            kk     < Thank you %(cba)s! You have successfully registered a birth for nancy on 01/01/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1-1 katrina
            kk     < Thank you %(cba)s! You have successfully registered a birth for katrina on 01/01/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1.1 molly
            kk     < Thank you %(cba)s! You have successfully registered a birth for molly on 01/01/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 1. 1 lisa
            kk     < Thank you %(cba)s! You have successfully registered a birth for lisa on 01/01/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 0101 lauren
            kk     < Thank you %(cba)s! You have successfully registered a birth for lauren on 01/01/%(year)s. You will be notified when it is time for his or her next appointment at the clinic.
        """ % {'year': datetime.datetime.now().year, 'cba': "Rupiah Banda"}
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(12, patients.count())
        for patient in patients:
            self.assertEqual(1, patient.patient_events.count())
            patient_event = patient.patient_events.get()
            self.assertEqual(patient_event.date, datetime.date(2012, 1, 1))
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
            kk     < Thank you Rupiah Banda! You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(1, patients.count())

    def testFacilityBirthRegistration(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="mwana", gender='f')
        reminders.Event.objects.create(name="Birth", slug="mwanaf", gender='f')
        script = """
            kk     > mwana f 4/3/2010 maria
            kk     < Thank you Rupiah Banda! You have successfully registered a facility birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > mwanaf 4/3/2010 Nelly Daka
            kk     < Thank you Rupiah Banda! You have successfully registered a facility birth for Nelly Daka on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(2, patients.count())
        
        self.assertEqual(2, reminders.PatientEvent.objects.filter(event_location_type='cl').count())

    def testCommunityBirthRegistration(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="mwana", gender='f')
        reminders.Event.objects.create(name="Birth", slug="mwanah ", gender='f')
        script = """
            kk     > mwana h 4/3/2010 maria
            kk     < Thank you Rupiah Banda! You have successfully registered a home birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > mwana h 4/3/2010 maria
            kk     < Thank you Rupiah Banda! You have successfully registered a home birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
            kk     > mwanah 4/3/2010 Nelly Daka
            kk     < Thank you Rupiah Banda! You have successfully registered a home birth for Nelly Daka on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(2, patients.count())

        self.assertEqual(2, reminders.PatientEvent.objects.filter(event_location_type='hm').count())

    def testFutureEventRegistration(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth", gender='f')
        script = """
            kk     > birth 4/6/2041 maria
            kk     < Sorry, you can not register a birth with a date after today's.
        """
        self.runScript(script)
        patients = Contact.objects.filter(types__slug='patient')
        self.assertEqual(0, patients.count())

    
class Reminders(TestScript):

    apps = (handler_app, App, )
    
    def testSendReminders(self):
        birth = reminders.Event.objects.create(name="Birth", slug="birth",
                                               gender="f")
        birth.appointments.create(name='2 day', num_days=2)
        birth.appointments.create(name='3 day', num_days=3)
        birth.appointments.create(name='4 day', num_days=4)
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
        appt_date = datetime.datetime.today() + datetime.timedelta(days=2)
        expected_messages = \
            ['Hi cba1.patient 1 is due for 2 day clinic visit on %s.'
             'Please remind them to visit Central Clinic, then '
             'reply with TOLD patient 1' % appt_date.strftime("%d/%m/%Y"),
             'Hi cba1.patient 2 is due for 2 day clinic visit on %s.'
             'Please remind them to visit Central Clinic, then '
             'reply with TOLD patient 2' % appt_date.strftime("%d/%m/%Y"),
             'Hi cba2.patient 3 is due for 2 day clinic visit on %s.'
             'Please remind them to visit Central Clinic, then '
             'reply with TOLD patient 3' % appt_date.strftime("%d/%m/%Y"),]
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
        appt_date = datetime.datetime.today() + datetime.timedelta(days=2)
        self.assertEqual(messages[0].text, "Hi Rupiah Banda.Henry is due "
                         "for 1 day clinic visit on %s.Please remind them to visit "
                         "the clinic, then reply with TOLD Henry" % appt_date.strftime("%d/%m/%Y"))
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
        appt_date = datetime.datetime.today() + datetime.timedelta(days=2)
        self.assertEqual(messages[0].text, "Hi cba.Henry is due for 1 day clinic visit on %s."
                                            "Please remind them to visit Central Clinic, "
                                            "then reply with TOLD Henry" % appt_date.strftime("%d/%m/%Y"))
        sent_notifications = reminders.SentNotification.objects.all()
        self.assertEqual(sent_notifications.count(), 1)        
        
class MockReminders(TestScript):

    apps = (handler_app, App, )
    def setUp(self):
        # this call is required if you want to override setUp
        super(MockReminders, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="400000")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="403000", parent = self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="402000", parent = self.luapula)
        self.mibenge = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="403029", parent = self.mansa, send_live_results=True)
        self.kashitu = Location.objects.create(type=self.type, name="Kashitu Clinic", slug="402026", parent = self.samfya, send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent = self.mansa, send_live_results=True)
        birth = reminders.Event.objects.create(name="Birth", slug="birth")

    def testSendMockReminders(self):
        """
        Tests mocking 6 day RemindMi messages to CBAs
        Reminders should only go to CBAs at specified facility
        """
        self.assertEqual(Contact.objects.count(), 0, "Contact list is not empty")

        #create different users - control and non control
        script = """
        luapula_pho > join pho 400000 Luapula PHO 1111
        mansa_dho > join dho 403000 Mansa DHO 1111
        samfya_dho > join dho 402000 Samfya DHO 1111
        mibenge_worker > join clinic 403029 Mibenge Man 1111
        kashitu_worker > join clinic 402026 kashitu Man 1111
        cental_worker > join clinic 403012 Central Man 1111
        mibenge_cba > join cba 403029 1 Mibenge CBA
        kashitu_cba > join cba 402026  2 kashitu cba
        central_cba1 > join cba 403012 3 Central cba1
        central_cba2 > join cba 403012 4 Central cba2
        demo_initiator > join pho 400000 Trainer Man 1111
        """

        self.runScript(script)
        self.assertEqual(Contact.objects.count(), 11)

        msgs=self.receiveAllMessages()
        
        self.assertEqual(11,len(msgs))

        from datetime import date, timedelta
        date = date.today() + timedelta(3)
        fdate = date.strftime('%d/%m/%Y')

        #only cba at given faclity should receive reminder. Default demo patient
        #is Maria Malambo
        script = """
        demo_initiator > rmdemo 402026
        kashitu_cba < Hi Kashitu Cba.Maria Malambo is due for 6 day clinic visit on %s.Please remind them to visit Kashitu Clinic, then reply with TOLD Maria Malambo
        """ % fdate
        self.runScript(script)

        # No extra messages
        msgs=self.receiveAllMessages()
        self.assertEqual(0,len(msgs))

        #only cba at given faclity should receive reminder. If baby is registered pick one
        script = """
        kashitu_cba > birth 29 06 2011 Groovy Phiri
        kashitu_cba < Thank you Kashitu Cba! You have successfully registered a birth for Groovy Phiri on 29/06/2011. You will be notified when it is time for his or her next appointment at the clinic.
        demo_initiator > rmdemo 402026
        kashitu_cba < Hi Kashitu Cba.Groovy Phiri is due for 6 day clinic visit on %s.Please remind them to visit Kashitu Clinic, then reply with TOLD Groovy Phiri
        """ % (fdate)
        self.runScript(script)

        # No extra messages
        msgs=self.receiveAllMessages()
        self.assertEqual(0,len(msgs))


        #Central clinic has two CBAs
        script = """
        demo_initiator > rmdemo 403012
        """
        self.runScript(script)

        # No extra messages
        msgs=self.receiveAllMessages()
        self.assertEqual(2,len(msgs))

        expected_msgs = [ "Hi Central Cba1.Maria Malambo is due for 6 day clinic visit on %s.Please remind them to visit Central Clinic, then reply with TOLD Maria Malambo" % fdate
        , "Hi Central Cba2.Maria Malambo is due for 6 day clinic visit on %s.Please remind them to visit Central Clinic, then reply with TOLD Maria Malambo" % fdate]

        for msg in msgs:
            self.assertTrue(msg.text in expected_msgs)
            self.assertTrue(msg.connection.identity in ["central_cba1", "central_cba2"],
            msg.connection.identity + " not in connection list" )
        
