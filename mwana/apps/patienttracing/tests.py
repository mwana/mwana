# vim: ai ts=4 sts=4 et sw=4
import json
from datetime import datetime,timedelta
import time
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Connection
from rapidsms.tests.scripted import TestScript
from mwana import const
from mwana.apps.patienttracing import app as App
from mwana.apps.patienttracing import models as patienttracing
from rapidsms.models import Contact
from mwana.apps.patienttracing.models import PatientTrace, SentConfirmationMessage
from mwana.apps.patienttracing import tasks

from rapidsms.contrib.handlers.app import App as handler_app


class TestApp(TestScript):
    def setUp(self):
        # this call is required if you want to override setUp
        super(TestApp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]        
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]        
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="luapula")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="mansa", parent = self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya", parent = self.luapula)
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="402029", parent = self.samfya)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent = self.mansa)

        
        self.support_clinic = Location.objects.create(type=self.type, name="Support Clinic", slug="spt")
        
        #create a clinic worker
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
        
        
        
        c_other_contact = Connection.objects.create(identity="other_worker", backend=connection.backend, 
                                  contact=self.other_contact)
        c_other_contact.save()

        #create a samfya clinic worker
        script = "clinic_worker_samfya > hello world"
        self.runScript(script)
        connection2 = Connection.objects.get(identity="clinic_worker_samfya")
        
        self.samfya_contact = Contact.objects.create(alias="sbanda", name="Samfya Banda", 
                                              location=self.samfya, pin="4567")
        self.samfya_contact.types.add(const.get_clinic_worker_type())
                                
        connection2.contact = self.samfya_contact
        connection2.save()

        # create CBA staff
        zone_type, _ = LocationType.objects.get_or_create(slug=const.ZONE_SLUGS[0])
        zone = Location.objects.create(name='002',
                                           parent=self.clinic,
                                           slug='002_02',
                                           type=zone_type)
        
        zone_samfya = Location.objects.create(name='00112',
                                                    parent=self.samfya,
                                                    slug='00112_01',
                                                    type=zone_type)
        
        self.cba_contact = Contact.objects.create(alias="cba1", name="Cba One",
                                                    location=zone, pin="1111", is_help_admin=False)
        self.cba_contact.types.add(const.get_cba_type())
        
        c_cba_contact = Connection.objects.create(identity="cba_contact", backend=connection.backend,
                                  contact=self.cba_contact)
        c_cba_contact.save()
        
        self.cba_contact2 = Contact.objects.create(alias='cba2', name='Cba Two',
                                                   location=zone_samfya, pin='1111',is_help_admin=False)
        self.cba_contact2.types.add(const.get_cba_type())
        
        c_cba_contact_2 = Connection.objects.create(identity='cba_contact2', backend=connection.backend,
                                  contact=self.cba_contact2)
        c_cba_contact_2.save()
        

    
    def testManualTrace(self):
#        self.assertEqual(0, PatientTrace.objects.count())

        script = """
            lost   > trace
            lost   < Sorry, the system could not understand your message. To trace a patient please send: TRACE <PATIENT_NAME>
            clinic_worker     > trace mary
            cba_contact       < Hi Cba One, please find mary and tell them to come to the clinic within 3 days. After telling them, reply with: TOLD mary
            clinic_worker     < Thank you John Banda. RemindMi Agents have been asked to find mary.
            """
        self.runScript(script)
        self.assertEqual(PatientTrace.objects.get(name='mary').status.lower(),"new")
            
        script = """
            cba_contact       > TOLD MARY
            clinic_worker     < Hi John Banda, CBA Cba One has just told MARY to come to the clinic.
            cba_contact       < Thank you Cba One! After you confirm MARY has visited the clinic, please send: CONFIRM MARY.
            
           """
        self.runScript(script)
        self.assertEqual(PatientTrace.objects.get(name__iexact='Mary').status.lower(),"told")
        
        script = """
            cba_contact       > Confirm Sarah
            cba_contact       < Thank you Cba One! You have confirmed that Sarah has been to the clinic!
            cba_contact       > Confirm Mary
            clinic_worker     < Hi John Banda, CBA Cba One has CONFIRMED that Mary has been to the clinic.
            cba_contact       < Thank you Cba One! You have confirmed that Mary has been to the clinic!
        """
        self.runScript(script)
        
        self.assertEqual(PatientTrace.objects.get(name__iexact='Mary').status.lower(),"confirmed")
        self.assertEqual(PatientTrace.objects.get(name__iexact='Sarah').status.lower(),"confirmed")
        

    apps = (handler_app, App, )
    
    def testSendConfirmReminders(self):
        #set up
        trace1 = self.create_new_patient_trace("bob", 
                                               self.cba_contact, 
                                               (datetime.now() - timedelta(days=6)), 
                                               (datetime.now() - timedelta(days=6)),
                                               self.contact)
        trace2 = self.create_new_patient_trace("suzy", 
                                               self.cba_contact, 
                                               datetime.now(), 
                                               datetime.now(),
                                               self.contact) #Shouldn't generate a confirm message because of date
        trace3 = self.create_new_patient_trace("pants", 
                                               self.cba_contact2,
                                               (datetime.now() - timedelta(days=6)), 
                                               (datetime.now() - timedelta(days=6)),
                                               self.samfya_contact)
                # this gets the backend and connection in the db
        self.runScript("""
        cba_contact > hello world
        cba_contact > hello world
        """)
        # take a break to allow the router thread to catch up; otherwise we
        # get some bogus messages when they're retrieved below
        time.sleep(.5)
        self.startRouter()
        time.sleep(.5)
        tasks.send_confirmation_reminder(self.router)
        # just the 2 traces should be of the right status and date
        # which means 2 messages should be captured
        messages = self.receiveAllMessages()
        expected_messages = \
            ['Hi Cba One! If you know that bob has been to the clinic, please send: CONFIRM bob',
             'Hi Cba Two! If you know that pants has been to the clinic, please send: CONFIRM pants',]
        self.assertEqual(len(messages), len(expected_messages))
        for msg in messages:
            self.assertTrue(msg.text in expected_messages, msg)
        sent_notifications = SentConfirmationMessage.objects.all()
        self.assertEqual(sent_notifications.count(), len(expected_messages))
        
        
    def create_new_patient_trace(self, pat_name, cba_contact, create_date, told_date, initiator=None):
        p = PatientTrace.objects.create(clinic = cba_contact.location.parent)
        p.initiator_contact = initiator
        p.messenger = cba_contact
        p.type="6 days"
        p.name = pat_name
        p.status = patienttracing.get_status_told()
        p.start_date = create_date
        p.reminded_date = told_date 
        p.save()
        return p
        
        
#    def testRemindersSentOnlyOnce(self):
#        """
#        tests that notification messages are sent only sent once
#        """
#        birth = reminders.Event.objects.create(name="Birth", slug="birth")
#        birth.appointments.create(name='1 day', num_days=2)
#        patient1 = Contact.objects.create(name='patient 1')
#        
#        # this gets the backend and connection in the db
#        self.runScript("""cba > hello world""")
#        # take a break to allow the router thread to catch up; otherwise we
#        # get some bogus messages when they're retrieved below
#        time.sleep(.1)
#        cba_conn = Connection.objects.get(identity="cba")
#        birth.patient_events.create(patient=patient1, cba_conn=cba_conn,
#                                    date=datetime.datetime.today())
#        self.startRouter()
#        tasks.send_notifications(self.router)
#        # just the 1 and two day notifications should go out;
#        # 3 patients x 2 notifications = 6 messages
#        messages = self.receiveAllMessages()
#        self.assertEqual(len(messages), 1)
#        sent_notifications = reminders.SentNotification.objects.all()
#        self.assertEqual(sent_notifications.count(), 1)
#
#        # make sure no new messages go out if the method is called again
#        tasks.send_notifications(self.router)
#        messages = self.receiveAllMessages()
#        self.assertEqual(len(messages), 0)
#        sent_notifications = reminders.SentNotification.objects.all()
#        # number of sent notifications should still be 1 (not 2)
#        self.assertEqual(sent_notifications.count(), 1)
#        
#        self.stopRouter()