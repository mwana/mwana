# vim: ai ts=4 sts=4 et sw=4
from datetime import timedelta
import time

from mwana.apps.alerts import tasks as smstasks
from mwana.apps.alerts.models import SMSAlertLocation
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.testdata.reports import *
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
import mwana.const as const
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript


class SMSAlertsSetUp(TestScript):

    def setUp(self):
        # this call is required if you want to override setUp
        super(SMSAlertsSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="400000")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="403000", parent=self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="402000", parent=self.luapula)
        self.kawambwa = Location.objects.create(type=self.type1, name="Kawambwa District", slug="401000", parent=self.luapula)
        self.mibenge = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="403029", parent=self.mansa, send_live_results=True)
        self.kashitu = Location.objects.create(type=self.type, name="Kashitu Clinic", slug="402026", parent=self.samfya, send_live_results=True)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent=self.mansa, send_live_results=True)
        self.salanga = Location.objects.create(type=self.type, name="Salanga Clinic", slug="401012", parent=self.kawambwa, send_live_results=True)

        self.assertEqual(SMSAlertLocation.objects.count(), 0)

        # Enable only mansa district to receive SMS alerts
        SMSAlertLocation.objects.create(enabled=True, district=self.mansa)
        SMSAlertLocation.objects.create(enabled=False, district=self.samfya)

        from datetime import datetime
        today = datetime.today()
        late = today - timedelta(days=60)

        # let clinics from different districts have pending results
        Result.objects.create(clinic=self.mibenge, arrival_date=late, result="N", notification_status='notified')
        Result.objects.create(clinic=self.salanga, arrival_date=late, result="N", notification_status='notified')
        Result.objects.create(clinic=self.mansa_central, arrival_date=late, result="N", notification_status='notified')

        # mark the clinic as having received results before (active)
        Result.objects.create(clinic=self.mibenge, arrival_date=late, result="N", notification_status='sent')
        Result.objects.create(clinic=self.salanga, arrival_date=late, result="N", notification_status='sent')
        Result.objects.create(clinic=self.mansa_central, arrival_date=late, result="N", notification_status='sent')

        # register staff for the clinics and also their districts and provinces
        self.assertEqual(Contact.objects.count(), 0, "Contact list is not empty")

        #create different users - control and non control
        script = """
        luapula_pho > join pho 400000 Luapula PHO 1111
        mansa_dho > join dho 403000 Mansa DHO 1111
        samfya_dho > join dho 402000 Samfya DHO 1111
        kawambwa_dho > join dho 401000 Kawambwa DHO 1111
        salanga_worker > join clinic 401012 Salanga Man 1111
        mibenge_worker > join clinic 403029 Mibenge Man 1111
        kashitu_worker > join clinic 402026 kashitu Man 1111
        central_worker > join clinic 403012 Central Man 1111
        mibenge_cba > join cba 403029 1 Mibenge CBA
        kashitu_cba > join cba 402026  2 kashitu cba
        central_cba1 > join cba 403012 3 Central cba1
        central_cba2 > join cba 403012 4 Central cba2
        """

        self.runScript(script)
        self.assertEqual(Contact.objects.count(), 12)

        msgs = self.receiveAllMessages()

        self.assertEqual(12, len(msgs))



    def tearDown(self):
        # this call is required if you want to override tearDown
        super(SMSAlertsSetUp, self).tearDown()


class TestSendingSMSAlerts(SMSAlertsSetUp):


    def testClinicsNotRetrievingResultsAlerts(self):

        time.sleep(.1)
        self.startRouter()
        smstasks.send_clinics_not_retrieving_results_alerts(self.router)
        msgs = self.receiveAllMessages()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].text, "ALERT! Mansa Dho, Clinics haven't retrieved results: Mibenge Clinic, Central "
                                       "Clinic. Please see https://mwana.moh.gov.zm/alerts for details")
        self.stopRouter()

    def testHubsNotSendingDbsAlerts(self):

        time.sleep(.1)
        self.startRouter()
        smstasks.send_hubs_not_sending_dbs_alerts(self.router)
        msgs = self.receiveAllMessages()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].text, "The Mansa District district hub (Unkown hub) has not sent samples to Unkown lab"
                                       " in over 11 days. Please see https://mwana.moh.gov.zm/alerts for details")
        self.stopRouter()

    def testClinicsNotSendingDbsAlerts(self):

        # from mansa district only central clinic used SENT keyword recently
        script = """
            central_worker> sent 5
            central_worker < Hello Central Man! We received your notification that 5 DBS samples were sent to us today from Central Clinic. We will notify you when the results are ready.
        """

        self.runScript(script)


        time.sleep(.1)
        self.startRouter()
        smstasks.send_clinics_not_sending_dbs_alerts(self.router)
        msgs = self.receiveAllMessages()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].text, "ALERT! Mansa Dho, Clinics haven't sent DBS to hub: Mibenge Clinic. Please "
                                       "see https://mwana.moh.gov.zm/alerts for details")
        self.stopRouter()

