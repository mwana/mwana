import datetime

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.locations.models import Location, LocationType

from mwana.apps.reminders.app import App
from mwana.apps.reminders import models as reminders


class TestApp(TestScript):
    apps = (handler_app, App,)
    
    def _register(self):
        ctr = LocationType.objects.create()
        Location.objects.create(name="Kafue District Hospital", slug="kdh",
                                type=ctr)
        script = """
            kk     > agent kdh 01 rupiah banda
            kk     < Thank you rupiah banda! You have successfully registered at as a RemindMi Agent for Kafue District Hospital.
            """
        self.runScript(script)
    
    def testRequiresRegistration(self):
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            noname > birth 4/3/2010 maria
            noname < Sorry you have to register to add events. To register as a RemindMi agent, send AGENT <CLINIC CODE> <ZONE #> <YOUR NAME>
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())
    
    def testMalformedMessage(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth
            kk     < Sorry, I didn't understand that. To add an event, send <EVENT CODE> <DATE> <NAME>.  The date is optional and is logged as TODAY if left out.
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())

    def testBadDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth 34553 maria
            kk     < Sorry, I couldn't understand that date. Please enter the date like so: DAY MONTH YEAR, for example: 23 04 2010
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())

    def testCorrectMessageWithDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth 4/3/2010 maria
            kk     < You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4 3 2010 laura
            kk     < You have successfully registered a birth for laura on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
            kk     > birth 4-3-2010 anna
            kk     < You have successfully registered a birth for anna on 04/03/2010. You will be notified when it is time for his or her next appointment at the clinic.
        """
        self.runScript(script)
        self.assertEqual(3, reminders.Patient.objects.count())
        for patient in reminders.Patient.objects.all():
            self.assertEqual(1, patient.patient_events.count())
            patient_event = patient.patient_events.get()
            self.assertEqual(patient_event.date, datetime.date(2010, 3, 4))
            self.assertEqual(patient_event.event.slug, "birth")

    def testCorrectMessageWithGender(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth", gender='f')
        script = """
            kk     > birth 4/3/2010 maria
            kk     < You have successfully registered a birth for maria on 04/03/2010. You will be notified when it is time for her next appointment at the clinic.
        """
        self.runScript(script)
        self.assertEqual(1, reminders.Patient.objects.count())
        
    def testCorrectMessageWithoutDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth maria
            kk     < You have successfully registered a birth for maria on %s. You will be notified when it is time for his or her next appointment at the clinic.
        """ % datetime.date.today().strftime('%d/%m/%Y')
        self.runScript(script)
        self.assertEqual(1, reminders.Patient.objects.count())
        patient = reminders.Patient.objects.get()
        self.assertEqual(1, patient.patient_events.count())
        patient_event = patient.patient_events.get()
        self.assertEqual(patient_event.date, datetime.date.today())
        self.assertEqual(patient_event.event.slug, "birth")
        
    def testAgentRegistration(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create()
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        reminders.Event.objects.create(name="Birth", slug="birth")
        self.assertEqual(reminders.Event.objects.count(), 1)
        script = """
            lost   > agent
            lost   < To register as a RemindMi agent, send AGENT <CLINIC CODE> <ZONE #> <YOUR NAME>
            rb     > agent kdh 01 rupiah banda
            rb     < Thank you rupiah banda! You have successfully registered at as a RemindMi Agent for Kafue District Hospital. Please notify us next time there is a birth in your zone.
            kk     > agent whoops 01 kenneth kaunda
            kk     < Sorry, I don't know about a location with code whoops. Please check your code and try again.
            noname > agent abc
            noname < Sorry, I didn't understand that. Make sure you send your clinic, zone #, and name like: AGENT <CLINIC CODE> <ZONE #> <YOUR NAME>
        """
        self.runScript(script)
        self.assertEqual(1, Contact.objects.count(), "Registration didn't create a new contact!")
        rb = Contact.objects.all()[0]
        self.assertEqual(rb.zone_code, 1)
        self.assertEqual("rupiah banda", rb.name, "Name was not set correctly after registration!")
        self.assertEqual(kdh, rb.location, "Location was not set correctly after registration!")

