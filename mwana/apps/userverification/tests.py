# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.reports.models import SupportedLocation
from mwana.apps.userverification.models import UserVerification
from datetime import timedelta
import time

from mwana.apps.userverification import tasks
from mwana.apps.labresults.testdata.reports import *
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
import mwana.const as const
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message



class UserVerificationSetUp(TestScript):

    def setUp(self):
        # this call is required if you want to override setUp
        super(UserVerificationSetUp, self).setUp()

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

        for loc in Location.objects.filter(type__singular="clinic"):
            SupportedLocation.objects.create(location =loc, supported =True)

        self.unsupported = Location.objects.create(type=self.type, name="Unsupported Clinic", slug="401013", parent=self.kawambwa, send_live_results=True)
             



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
        unsupported_worker > join clinic 403013 I Man 1111
        mibenge_cba > join cba 403029 1 Mibenge CBA
        kashitu_cba > join cba 402026  2 kashitu cba
        central_cba1 > join cba 403012 3 Central cba1
        central_cba2 > join cba 403012 4 Central cba2
        """

        self.runScript(script)
        self.assertEqual(Contact.objects.count(), 12)

        msgs = self.receiveAllMessages()

        self.assertEqual(13, len(msgs))



    def tearDown(self):
        # this call is required if you want to override tearDown
        super(UserVerificationSetUp, self).tearDown()


class TestUserVerications(UserVerificationSetUp):


    def testSendingOnlyToClinicWorkers(self):
        """
        Only clinic workers should receive user verification messages
        """

        self.assertEqual(UserVerification.objects.count(), 0, "User verication model is not empty")
        time.sleep(.1)

        self.startRouter()
        tasks.send_verification_request(self.router)
        msgs = self.receiveAllMessages()

        expected_recipients = ["salanga_worker", "mibenge_worker", "kashitu_worker", "central_worker"]
        expected_msgs = """Hello Salanga Man. Are you still working at Salanga Clinic and still using Results160? Please respond with YES or No
Hello Mibenge Man. Are you still working at Mibenge Clinic and still using Results160? Please respond with YES or No
Hello Kashitu Man. Are you still working at Kashitu Clinic and still using Results160? Please respond with YES or No
Hello Central Man. Are you still working at Central Clinic and still using Results160? Please respond with YES or No
        """
        for msg in msgs:
            self.assertTrue(msg.connection.identity in expected_recipients, "%s not in expected recipients" %msg.connection.identity)
            self.assertTrue(msg.text in expected_msgs.split("\n"), "%s not in expected messages" %msg.text)


        self.assertEqual(len(msgs), 4)
        self.stopRouter()

    def testSendingOnlyOnceInAPeriod(self):
        """
        defaulting clinic workers should receive user verification messages only
        once in a period
        """

        self.assertEqual(UserVerification.objects.count(), 0, "User verication model is not empty")
        time.sleep(.1)

        self.startRouter()
        tasks.send_verification_request(self.router)
        tasks.send_verification_request(self.router)
        msgs = self.receiveAllMessages()

        expected_recipients = ["salanga_worker", "mibenge_worker", "kashitu_worker", "central_worker"]
        expected_msgs = """Hello Salanga Man. Are you still working at Salanga Clinic and still using Results160? Please respond with YES or No
Hello Mibenge Man. Are you still working at Mibenge Clinic and still using Results160? Please respond with YES or No
Hello Kashitu Man. Are you still working at Kashitu Clinic and still using Results160? Please respond with YES or No
Hello Central Man. Are you still working at Central Clinic and still using Results160? Please respond with YES or No
        """
        for msg in msgs:
            self.assertTrue(msg.connection.identity in expected_recipients, "%s not in expected recipients" %msg.connection.identity)
            self.assertTrue(msg.text in expected_msgs.split("\n"), "%s not in expected messages" %msg.text)


        self.assertEqual(len(msgs), 4)
        self.stopRouter()

    def testSendingOnlyToDefautingClinicWorkers(self):
        """
        Only defaulting clinic workers should receive user verification messages
        """

        script = """
        central_worker > i use the system
        """
        self.runScript(script)
        self.assertEqual(UserVerification.objects.count(), 0, "User verification model is not empty")
        time.sleep(.1)

        self.startRouter()
        tasks.send_verification_request(self.router)
        msgs = self.receiveAllMessages()

        expected_recipients = ["salanga_worker", "mibenge_worker", "kashitu_worker"]
        expected_msgs = """Hello Salanga Man. Are you still working at Salanga Clinic and still using Results160? Please respond with YES or No
Hello Mibenge Man. Are you still working at Mibenge Clinic and still using Results160? Please respond with YES or No
Hello Kashitu Man. Are you still working at Kashitu Clinic and still using Results160? Please respond with YES or No
        """
        for msg in msgs:
            self.assertTrue(msg.connection.identity in expected_recipients, "%s not in expected recipients" %msg.connection.identity)
            self.assertTrue(msg.text in expected_msgs.split("\n"), "%s not in expected messages" %msg.text)


        self.assertEqual(len(msgs), 3)
        self.stopRouter()

        # let's fake that central_worker used the system a very long time ago
        msg = Message.objects.get(direction="I", contact__name="Central Man", connection__identity="central_worker")
        msg.date = today - timedelta(days = 100)
        msg.save()
        msg.delete()
        

        self.assertEqual(UserVerification.objects.count(), 3, "Number of User verications not equal")

        time.sleep(.1)
        self.startRouter()

        tasks.send_verification_request(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(len(msgs), 1)

        self.assertEqual(msgs[0].connection.identity, "central_worker", "Message was sent to wrong recipient")
        self.assertEqual(msgs[0].text, "Hello Central Man. Are you still working at Central Clinic and still using Results160? Please respond with YES or No", "Message not as expected")

        self.assertEqual(UserVerification.objects.count(), 4, "Number of User verications not equal")


    def testUserVerificationWorkflow(self):

        self.assertEqual(UserVerification.objects.count(), 0, "User verification model is not empty")
        time.sleep(.1)

        self.startRouter()
        tasks.send_verification_request(self.router)
        msgs = self.receiveAllMessages()

        expected_recipients = ["salanga_worker", "mibenge_worker", "kashitu_worker", "central_worker"]
        expected_msgs = """Hello Salanga Man. Are you still working at Salanga Clinic and still using Results160? Please respond with YES or No
Hello Mibenge Man. Are you still working at Mibenge Clinic and still using Results160? Please respond with YES or No
Hello Kashitu Man. Are you still working at Kashitu Clinic and still using Results160? Please respond with YES or No
Hello Central Man. Are you still working at Central Clinic and still using Results160? Please respond with YES or No
        """
        for msg in msgs:
            self.assertTrue(msg.connection.identity in expected_recipients, "%s not in expected recipients" %msg.connection.identity)
            self.assertTrue(msg.text in expected_msgs.split("\n"), "%s not in expected messages" %msg.text)


        self.assertEqual(len(msgs), 4)
        self.stopRouter()

        script = """
        salanga_worker > yes
        mibenge_worker > no
        kashitu_worker > i do
        central_worker > some message
        """

        self.runScript(script)

        self.assertTrue(0==len(self.receiveAllMessages()))
        
        self.assertEqual(UserVerification.objects.count(), 4, "User verications not equal to 4")
        self.assertEqual(UserVerification.objects.filter(response="yes").count(), 1, "User verications not equal to 1")
        self.assertEqual(UserVerification.objects.filter(response="no").count(), 1, "User verications not equal to 1")
        self.assertEqual(UserVerification.objects.filter(response="i do").count(), 1, "User verications not equal to 1")
        self.assertEqual(UserVerification.objects.filter(response="some message").count(), 1, "User verications not equal to 1")



    def testFinalUserVerificationWorkflow(self):

        self.assertEqual(UserVerification.objects.count(), 0, "User verification model is not empty")
        time.sleep(.1)

        self.startRouter()
        tasks.send_verification_request(self.router)
        msgs = self.receiveAllMessages()

        expected_recipients = ["salanga_worker", "mibenge_worker", "kashitu_worker", "central_worker"]
        expected_msgs = """Hello Salanga Man. Are you still working at Salanga Clinic and still using Results160? Please respond with YES or No
Hello Mibenge Man. Are you still working at Mibenge Clinic and still using Results160? Please respond with YES or No
Hello Kashitu Man. Are you still working at Kashitu Clinic and still using Results160? Please respond with YES or No
Hello Central Man. Are you still working at Central Clinic and still using Results160? Please respond with YES or No
        """
        for msg in msgs:
            self.assertTrue(msg.connection.identity in expected_recipients, "%s not in expected recipients" %msg.connection.identity)
            self.assertTrue(msg.text in expected_msgs.split("\n"), "%s not in expected messages" %msg.text)


        self.assertEqual(len(msgs), 4)
        self.stopRouter()

        script = """
        salanga_worker > yes
        mibenge_worker > no
        """

        self.runScript(script)

        self.assertTrue(0==len(self.receiveAllMessages()))

        self.assertEqual(UserVerification.objects.count(), 4, "User verications not equal to 4")
        self.assertEqual(UserVerification.objects.filter(response="yes").count(), 1, "User verications not equal to 1")
        self.assertEqual(UserVerification.objects.filter(response="no").count(), 1, "User verications not equal to 1")

        time.sleep(.1)
        self.startRouter()
        tasks.send_final_verification_request(self.router)
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(UserVerification.objects.count(), 6, "User verications not equal to 6")
        for msg in msgs:
            self.assertTrue(msg.connection.identity in expected_recipients, "%s not in expected recipients" %msg.connection.identity)
            self.assertTrue(msg.text in expected_msgs.split("\n"), "%s not in expected messages" %msg.text)


        self.assertEqual(len(msgs), 2)

        time.sleep(.1)
        self.startRouter()


        self.assertEqual(Contact.objects.filter(is_active=False).count(), 1)
        tasks.inactivate_lost_users(self.router)

        self.assertEqual(Contact.objects.filter(is_active=False).count(), 3)
