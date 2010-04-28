import time

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.locations.models import Location, LocationType

from mwana.apps.tracing.app import App
from mwana.apps.tracing import models as tracing
from mwana import const


class TestApp(TestScript):
    apps = (handler_app, App,)
    
    def testTrace(self):
        zone = LocationType.objects.create(slug='zone')
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=zone)
        # this gets the backend and connection in the db
        self.runScript("""
            rb > hello world
            cba > hello world
        """)
        # take a break to allow the router thread to catch up; otherwise we
        # get some bogus messages when they're retrieved below
        time.sleep(.1)
        rb = Connection.objects.get(identity='rb')
        rb.contact = Contact.objects.create(name='Rupiah Banda', location=kdh)
        rb.contact.types.add(const.get_clinic_worker_type())
        rb.save()
#        script = """
#            rb     > trace maria
#            rb     < I'm sorry, Rupiah Banda. I couldn't find any RemindMi agents to trace maria.
#         """
#        self.runScript(script)
        
        rb = Connection.objects.get(identity='cba')
        rb.contact = Contact.objects.create(name='John', location=kdh)
        rb.contact.types.add(const.get_cba_type())
        rb.save()
        script = """
            lost   > trace
            lost   < To trace a patient, send TRACE <PATIENT NAME> ZONE <ZONE>. The zone is optional and the notification will be sent to all CBAs for this clinic if it is left out.
            rb     > trace maria
            cba    < Hello John. maria is due for his or her next clinic appointment. Please deliver a reminder to this person and ensure he or she visits Kafue District Hospital within 3 days.
            rb     < Thank you Rupiah Banda. I have sent a message to the responsible RemindMi agents to trace maria and tell him or her to come to the clinic.
            rb     > trace leah zone kdh
            cba    < Hello John. leah is due for his or her next clinic appointment. Please deliver a reminder to this person and ensure he or she visits Kafue District Hospital within 3 days.
            rb     < Thank you Rupiah Banda. I have sent a message to the responsible RemindMi agents to trace leah and tell him or her to come to the clinic.
            rb     > trace john james
            cba    < Hello John. john james is due for his or her next clinic appointment. Please deliver a reminder to this person and ensure he or she visits Kafue District Hospital within 3 days.
            rb     < Thank you Rupiah Banda. I have sent a message to the responsible RemindMi agents to trace john james and tell him or her to come to the clinic.
            rb     > trace joe fischer zone kdh
            cba    < Hello John. joe fischer is due for his or her next clinic appointment. Please deliver a reminder to this person and ensure he or she visits Kafue District Hospital within 3 days.
            rb     < Thank you Rupiah Banda. I have sent a message to the responsible RemindMi agents to trace joe fischer and tell him or her to come to the clinic.
        """
        self.runScript(script)
        self.assertEqual(4, Contact.objects.filter(types__slug='patient').count(),
                         "Tracing didn't create the right number of contacts!")
        self.assertEqual(4, tracing.Trace.objects.count())
        
        
