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
    
    testRequiresRegistration = """
        noname > event a b c d
        noname < Sorry you have to register to add events. To register, send JOIN <LOCATION CODE> <NAME>
    """
    
    def testMalformedMessage(self):
        self._register()
        script = """
            kk     > event a b c
            kk     < Sorry, I didn't understand that. To add an event, send EVENT <EVENT CODE> <DATE> <NAME> <LOCATION>
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())
    
    def testBadEvent(self):
        self._register()
        script = """
            kk     > event whoops 3/3 maria kdh
            kk     < Sorry, I don't know about an event with code whoops. Please check your code and try again.
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())
        
    def testBadLocation(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > event birth 3/3 maria whoops
            kk     < Sorry, I don't know about a location with code whoops. Please check your code and try again.
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())
        
    def testBadDate(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > event birth 34553 maria kdh
            kk     < Sorry, I couldn't understand that date. Please enter the date like so: DAY/MONTH/YEAR, like so: 23/04/2010
        """
        self.runScript(script)
        self.assertEqual(0, reminders.Patient.objects.count())
        
    def testCorrectMessage(self):
        self._register()
        reminders.Event.objects.create(name="Birth", slug="birth")
        script = """
            kk     > event birth 4/3/2010 maria kdh
            kk     < Thank you for adding a Birth for maria.  You will be notified when it's time for his or her next appointment.
        """
        self.runScript(script)
        self.assertEqual(1, reminders.Patient.objects.count())
        patient = reminders.Patient.objects.get()
        self.assertEqual(patient.location.slug, "kdh")
        self.assertEqual(1, patient.patient_events.count())
        patient_event = patient.patient_events.get()
        self.assertEqual(patient_event.date, datetime.date(2010, 3, 4))
        self.assertEqual(patient_event.event.slug, "birth")
        
