import time

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.locations.models import Location, LocationType

from mwana.apps.tracing.app import App
from mwana.apps.tracing import models as tracing


class TestApp(TestScript):
    apps = (handler_app, App,)
    
    def testTrace(self):
        zone = LocationType.objects.create(slug='zone')
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=zone)
        # this gets the backend and connection in the db
        self.runScript("""rb > hello world""")
        # take a break to allow the router thread to catch up; otherwise we
        # get some bogus messages when they're retrieved below
        time.sleep(.1)
        rb = Connection.objects.get(identity='rb')
        rb.contact = Contact.objects.create(name='Rupiah Banda', location=kdh)
        rb.save()
        script = """
            lost   > trace
            lost   < To trace a patient, send TRACE <PATIENT NAME> VIA <ZONE>. The zone is optional and the notification will be sent to all CBAs for this clinic if it is left out.
            rb     > trace maria
            rb     < Thank you Rupiah Banda. I will send a message to the responsible RemindMi agents to trace  and tell him or her to come to the clinic.
            rb     > trace leah via kdh
            rb     < Thank you Rupiah Banda. I will send a message to the responsible RemindMi agents to trace  and tell him or her to come to the clinic.
        """
        self.runScript(script)
        self.assertEqual(2, Contact.objects.filter(types__slug='patient').count(),
                         "Tracing didn't create the right number of contacts!")
        self.assertEqual(2, tracing.Trace.objects.count())
