# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.hub_workflow.models import HubSampleNotification

import mwana.const as const
from django.conf import settings
from mwana.apps.labresults.models import SampleNotification
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.tests.scripted import TestScript
from mwana.apps.labresults.testdata.reports import *


class LabresultsSetUp(TestScript):

    def _result_text(self):
        """
        Returns the appropriate display value for DBS results as it would
        appear in an SMS.
        """
        results_text = getattr(settings, 'RESULTS160_RESULT_DISPLAY', {})
        results = {'detected': results_text.get('P', 'Detected'),
                   'not_detected': results_text.get('N', 'NotDetected')}
        return results

    def setUp(self):
        # this call is required if you want to override setUp
        super(LabresultsSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="luapula")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="mansa", parent = self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya", parent = self.luapula)
        self.mibenge = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="403029", parent = self.mansa, send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent = self.mansa, send_live_results=True)
       
        self.support_clinic = Location.objects.create(type=self.type, name="Support Clinic", slug="spt")      


    def tearDown(self):
        # this call is required if you want to override tearDown
        super(LabresultsSetUp, self).tearDown()
        try:
            self.clinic.delete()
            self.mansa.delete()
            self.type.delete()
            self.client.logout()
        except:
            pass
            #TODO catch specific exception
    

class TestApp(LabresultsSetUp):  

    def testSentNotifications(self):
        self.assertEqual(0, HubSampleNotification.objects.count())
        script = """
            hub_worker > join hub 403012 hubman phiri 1111
            hub_worker < Hi Hubman Phiri, thanks for registering for Results160 from hub at Central Clinic. Your PIN is 1111. Reply with keyword 'HELP' if this is incorrect
            clinic_worker > join clinic 403029 james banda 1111
            clinic_worker < Hi James Banda, thanks for registering for Results160 from Mibenge Clinic. Your PIN is 1111. Reply with keyword 'HELP' if this is incorrect
        """
        self.runScript(script)

        script = """
            clinic_worker > SENT 5
            hub_worker < Hello Hubman Phiri! Mibenge Clinic have sent 5 samples to Central Clinic hub today.
            clinic_worker < Hello James Banda! We received your notification that 5 DBS samples were sent to us today from Mibenge Clinic. We will notify you when the results are ready.
        """
        self.runScript(script)
        script = """
            hub_worker > SENT 6
            hub_worker < Hello Hubman Phiri! We received your notification that 6 DBS samples were sent to us today from Central Clinic hub.
        """
        self.runScript(script)
        
        self.assertEqual(1, HubSampleNotification.objects.all().count())
        self.assertEqual(1, HubSampleNotification.objects.filter(lab=self.mansa_central).count())
        sample_notification = HubSampleNotification.objects.get(pk=1)
        self.assertEqual(6, sample_notification.count)
        self.assertEqual("Hubman Phiri", sample_notification.contact.name)

    def testReceivedNotifications(self):
        self.assertEqual(0, SampleNotification.objects.count())
        script = """
            hub_worker > join hub 403012 hubman phiri 1111
            hub_worker < Hi Hubman Phiri, thanks for registering for Results160 from hub at Central Clinic. Your PIN is 1111. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)

        script = """
            hub_worker > receive 6 403029
            hub_worker < Hello Hubman Phiri! We received your notification that you received 6  DBS samples today from Mibenge Clinic.
            hub_worker > receive six 403029
            hub_worker < Hello Hubman Phiri! We received your notification that you received 6  DBS samples today from Mibenge Clinic.
        """
        self.runScript(script)

        self.assertEqual(2, HubSampleNotification.objects.all().count())
        sample_notification = HubSampleNotification.objects.get(pk=1)
        self.assertEqual(6, sample_notification.count)
        self.assertEqual("Hubman Phiri", sample_notification.contact.name)

