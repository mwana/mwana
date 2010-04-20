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
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        script = """
            kk     > join kdh rupiah banda
            kk     < Thank you for registering, rupiah banda! I've got you at Kafue District Hospital.
        """
        self.runScript(script)
    
    def testRequiresRegistration(self):
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            noname > birth 4/3/2010 maria
            noname < Sorry you have to register to add events. To register, send JOIN <LOCATION CODE> <NAME>
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
            kk     < Sorry, I couldn't understand that date. Please enter the date like so: DAY/MONTH/YEAR, for example: 23/04/2010
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())
        
    def testCorrectMessageWithDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth 4/3/2010 maria
            kk     < Thank you for adding a birth for maria on 04/03/2010.  You will be notified when it's time for his or her next appointment.
        """
        self.runScript(script)
        self.assertEqual(1, reminders.Patient.objects.count())
        patient = reminders.Patient.objects.get()
        self.assertEqual(1, patient.patient_events.count())
        patient_event = patient.patient_events.get()
        self.assertEqual(patient_event.date, datetime.date(2010, 3, 4))
        self.assertEqual(patient_event.event.slug, "birth")
        
    def testCorrectMessageWithoutDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > birth maria
            kk     < Thank you for adding a birth for maria on %s.  You will be notified when it's time for his or her next appointment.
        """ % datetime.date.today().strftime('%d/%m/%Y')
        self.runScript(script)
        self.assertEqual(1, reminders.Patient.objects.count())
        patient = reminders.Patient.objects.get()
        self.assertEqual(1, patient.patient_events.count())
        patient_event = patient.patient_events.get()
        self.assertEqual(patient_event.date, datetime.date.today())
        self.assertEqual(patient_event.event.slug, "birth")
        
