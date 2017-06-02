# vim: ai ts=4 sts=4 et sw=4
import time

from datetime import timedelta
from rapidsms.models import Connection
from rapidsms.tests.scripted import TestScript

import mwana.const as const
from mwana.apps.anc.models import EducationalMessage
from mwana.apps.anc.messages import EDUCATIONAL_MESSAGES
from mwana.apps.anc.messages import WELCOME_MSG_A
from mwana.apps.anc.messages import WELCOME_MSG_B
from mwana.apps.anc.models import Client
from mwana.apps.anc.models import SentMessage
from mwana.apps.anc import tasks
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType


class AncSetUp(TestScript):
    def setUp(self):
        # this call is required if you want to override setUp
        super(AncSetUp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[
            0]

        self.clinic = Location.objects.create(type=self.type, name="Chelston", slug="101010",
                                              send_live_results=True)

    def tearDown(self):
        # this call is required if you want to override tearDown
        super(AncSetUp, self).tearDown()
        self.clinic.delete()
        self.type.delete()


class TestApp(AncSetUp):
    def create_client(self, client_con='client', gestational_age=8):
        """
        Utility method to create client.
        :param client_con: 
        :param gestational_age: 
        """
        script = """
            {client} > ANC 101010 {age}
            {client} < You have successfully subscribed from Chelston clinic and your gestational age is {age}. Resubmit if this is incorrect
            {client} < {msg1}
            {client} < {msg2}
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B, client=client_con, age=gestational_age)
        self.runScript(script)

    def create_educational_messages(self):
        for item in EDUCATIONAL_MESSAGES:
            EducationalMessage.objects.get_or_create(gestational_age=item[0], text=item[1])

    def testGestationAgeInvalid(self):
        script = """
            client > ANC 101010 x8
            client < Sorry, I didn't understand that. To subscribe, Send ANC <CLINIC-CODE> <GESTATIONAL-AGE IN WEEKS>, E.g. ANC 504033 8
            client > ANC 101010 50
            client < Sorry you cannot subscribe when your gestational age is already 40 or above
        """
        self.runScript(script)

    def testMalformedMessage(self):
        script = """
            client > ANC 101010
            client < Sorry, I didn't understand that. To subscribe, Send ANC <CLINIC-CODE> <GESTATIONAL-AGE IN WEEKS>, E.g. ANC 504033 8
            client > ANC 50
            client < Sorry, I didn't understand that. To subscribe, Send ANC <CLINIC-CODE> <GESTATIONAL-AGE IN WEEKS>, E.g. ANC 504033 8
            client > ANC 101010 -5 4
            client < Sorry, I didn't understand that. To subscribe, Send ANC <CLINIC-CODE> <GESTATIONAL-AGE IN WEEKS>, E.g. ANC 504033 8
        """
        self.runScript(script)

    def testUnkownLocation(self):
        script = """
            client > ANC 4444 5
            client < Sorry, I don't know about a location with code 4444. Please check your code and try again.
            """
        self.runScript(script)

    def testRegistration(self):
        script = """
            client > ANC 101010 8
            client < You have successfully subscribed from Chelston clinic and your gestational age is 8. Resubmit if this is incorrect
            client < {msg1}
            client < {msg2}
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B)
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(8))
        self.assertEqual(client.gestation_at_subscription, 8)
        self.assertEqual(client.connection.identity, 'client')
        self.assertEqual(client.facility, self.clinic)

        # Test resubmission with same gestational period
        client.status = 'deprecated'
        client.save()
        script = """
            client > ANC 101010 10
            client < You have successfully subscribed from Chelston clinic and your gestational age is 10. Resubmit if this is incorrect
            client < {msg1}
            client < {msg2}
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B)
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(10))
        self.assertEqual(client.gestation_at_subscription, 10)
        self.assertEqual(client.connection.identity, 'client')
        self.assertEqual(client.facility, self.clinic)

        # Test resubmission with different gestational period
        client.lmp = client.lmp - timedelta(days=41 * 7)
        client.save()
        script = """
            client > ANC 101010 12
            client < You have successfully subscribed from Chelston clinic and your gestational age is 12. Resubmit if this is incorrect
            client < {msg1}
            client < {msg2}
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B)
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 2)
        client = Client.objects.get(pk=2)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(12))
        self.assertEqual(client.gestation_at_subscription, 12)
        self.assertEqual(client.connection.identity, 'client')
        self.assertEqual(client.facility, self.clinic)

    def testNegativeGestationAge(self):
        script = """
            client > ANC 101010 -8
            client < You have successfully subscribed from Chelston clinic and your gestational age is 8. Resubmit if this is incorrect
            client < {msg1}
            client < {msg2}
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B)
        self.runScript(script)

    def testSendANCMessages(self):
        self.create_educational_messages()
        gestational_ages = [item[0] for item in EDUCATIONAL_MESSAGES]

        for age in gestational_ages:
            if age >= 40:  # get around validation
                backend = Connection.objects.get(pk=1).backend
                conn, _ = Connection.objects.get_or_create(identity="client%s" % age, backend=backend)

                Client.objects.get_or_create(gestation_at_subscription=age,
                                             lmp=Client.find_lmp(age), facility=self.clinic,
                                             connection=conn)
                # self.create_client(client_con="client%s" % age, gestational_age=age-40)
                # client = Client.objects.get(connection__identity="client%s" % age, gestation_at_subscription=age-40)
                # client.lmp = Client.find_lmp(age)
                # client.gestation_at_subscription = age
                # client.save()
            else:
                self.create_client(client_con="client%s" % age, gestational_age=age)

        self.assertEqual(SentMessage.objects.count(), 0)

        time.sleep(.2)
        # start router and send a notification
        self.startRouter()
        tasks.send_anc_messages(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(SentMessage.objects.count(), len(gestational_ages))

        for item in EDUCATIONAL_MESSAGES:
            self.assertTrue(SentMessage.objects.filter(client__connection__identity="client%s" % item[0],
                                                       message__text=item[1]).exists(), 'Not found %s' % item[1])

    def testStatusMessage(self):
        self.create_client()
        client = Client.objects.get()
        client.status = ''
        # run task
        script = """
            client > Thank you
            client > Received
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B)
        self.runScript(script)

    def testIgnoreHandleInvalidMessage(self):
        self.create_client()
        script = """
            client > Thank you
            client > Received
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B)
        self.runScript(script)

    def testCleanMessage(self):
        self.create_client()
        script = """
            client > ANC 101010 14 weeks
            client > Received
        """.format(msg1=WELCOME_MSG_A, msg2=WELCOME_MSG_B)
        self.runScript(script)
