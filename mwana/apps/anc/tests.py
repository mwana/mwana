# vim: ai ts=4 sts=4 et sw=4
import time

from datetime import timedelta

from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Connection
from rapidsms.tests.scripted import TestScript

import mwana.const as const
from mwana.apps.anc.models import SentCHWMessage
from mwana.apps.anc.models import FlowCommunityWorkerRegistration, CommunityWorker
from mwana.apps.anc.models import WaitingForResponse
from mwana.apps.anc.models import EducationalMessage
from mwana.apps.anc.messages import EDUCATIONAL_MESSAGES
from mwana.apps.anc.messages import WELCOME_MSG_A
from mwana.apps.anc.messages import WELCOME_MSG_B
from mwana.apps.anc.models import Client
from mwana.apps.anc.models import SentClientMessage
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
        self.zone_type = LocationType.objects.get_or_create(singular="zone", plural="zone", slug=const.ZONE_SLUGS[0])[0]
        self.zone = Location.objects.create(type=self.zone_type, name='3', slug='zone')

    def vtearDown(self):
        # this call is required if you want to override tearDown
        super(AncSetUp, self).tearDown()
        self.clinic.delete()
        self.type.delete()


class TestApp(AncSetUp):
    def create_chw(self, chw_con='chw'):
        script = """
               {chw} > CHW
               {chw} < Welcome to the Mother Baby Service Reminder Program. To register as a CHW reply with your name.
               {chw} > Donald Clinton
               {chw} < Thank you Donald Clinton. Now reply with your clinic code
               {chw} > 101010
               {chw} < Your clinic is Chelston. Now reply with your zone name
               {chw} > 3
               {chw} < Donald Clinton you have successfully joined as CHW for the Mother Baby Service Reminder Program from zone 3 of Chelston clinic. If this is not correct register again
           """.format(chw=chw_con)
        self.runScript(script)
        return CommunityWorker.objects.get(connection__identity=chw_con)

    def create_client(self, client_con='client', gestational_age=8, community_worker=None):
        """
        Utility method to create client.
        :param client_con: 
        :param gestational_age: 
        """

        script = """
            {client} > blah blah 101010
            {client} < Please send the keyword HELP if you need to be assisted.
        """.format(client=client_con)
        self.runScript(script)
        client = Client(connection=Connection.objects.get(identity=client_con),
                        gestation_at_subscription=gestational_age,
                        facility=self.clinic, phone_confirmed=True, community_worker=community_worker)
        client.lmp = Client.find_lmp(gestational_age)
        client.status = 'pregnant'
        client.save()
        return client

    def create_educational_messages(self):
        for item in EDUCATIONAL_MESSAGES:
            EducationalMessage.objects.get_or_create(gestational_age=item[0], text=item[1])

    def testCHWRegistration(self):
        script = """
            chw > CHW
            chw < Welcome to the Mother Baby Service Reminder Program. To register as a CHW reply with your name.
            chw > Donald Clinton
            chw < Thank you Donald Clinton. Now reply with your clinic code
            chw > 101010
            chw < Your clinic is Chelston. Now reply with your zone name
            chw > 3
            chw < Donald Clinton you have successfully joined as CHW for the Mother Baby Service Reminder Program from zone 3 of Chelston clinic. If this is not correct register again
        """
        self.runScript(script)
        self.assertEqual(0, FlowCommunityWorkerRegistration.objects.count())
        chw = CommunityWorker.objects.get(pk=1)
        self.assertEqual(chw.connection.identity, 'chw')
        self.assertEqual(chw.name, 'Donald Clinton')
        self.assertEqual(chw.zone, '3')
        self.assertEqual(chw.is_active, True)
        self.assertEqual(chw.facility, self.clinic)
        self.assertEqual(CommunityWorker.objects.all().count(), 1)

    def testCHWRegistrationErrorHandling(self):
        script = """
            chw > CHW 101010 x8
            chw < Welcome to the Mother Baby Service Reminder Program. To register as a CHW reply with your name.
            chw > Donald Clinton
            chw < Thank you Donald Clinton. Now reply with your clinic code
            chw > okay
            chw < Sorry, I don't know about a clinic with code okay. Please check your code and try again.
            chw > zone
            chw < Sorry, I don't know about a clinic with code zone. Please check your code and try again.
            chw > 1010105
            chw < Your clinic is Chelston. Now reply with your zone name
            chw > 3
            chw < Donald Clinton you have successfully joined as CHW for the Mother Baby Service Reminder Program from zone 3 of Chelston clinic. If this is not correct register again
            chw > CHW
            chw < Your phone is already registered to Donald Clinton of Chelston health facility. Send HELP CHW if you need to be assisted 
            chw > 55555
            chw < You have successfully unsubscribed Donald Clinton.
            chw > CHW
            chw < Welcome to the Mother Baby Service Reminder Program. To register as a CHW reply with your name.
            chw > Hillary Trump
            chw < Thank you Hillary Trump. Now reply with your clinic code
            chw > 101010
            chw < Your clinic is Chelston. Now reply with your zone name
            chw > lovely
            chw < Hillary Trump you have successfully joined as CHW for the Mother Baby Service Reminder Program from zone lovely of Chelston clinic. If this is not correct register again        
        """
        self.runScript(script)
        self.assertEqual(0, FlowCommunityWorkerRegistration.objects.count())
        chw = CommunityWorker.objects.get(pk=1)
        self.assertEqual(chw.connection.identity, 'chw')
        self.assertEqual(chw.name, 'Donald Clinton')
        self.assertEqual(chw.zone, '3')
        self.assertEqual(chw.is_active, False)
        self.assertEqual(chw.facility, self.clinic)
        chw = CommunityWorker.objects.get(pk=2)
        self.assertEqual(chw.connection.identity, 'chw')
        self.assertEqual(chw.name, 'Hillary Trump')
        self.assertEqual(chw.zone, 'lovely')
        self.assertEqual(chw.is_active, True)
        self.assertEqual(chw.facility, self.clinic)
        self.assertEqual(CommunityWorker.objects.all().count(), 2)

    def testRegistration(self):
        self.create_chw(chw_con='+260979112233')
        script = """
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 0977123456
            +260979112233 < You have submitted mum's phone number +260977123456. Now reply with the mum's gestational age
            +260979112233 > 8
            +260979112233 < Mother's phone number is +260977123456 and gestational age is 8. Reply with Yes if this is correct or No if not
            +260979112233 > Yes
            +260977123456 < Welcome to the Mother Baby Service Reminder. Reply with YES if you are 8 weeks pregnant and want to receive SMS reminders about ANC. Or reply with AGE + the number of weeks if 8 is not correct. Kind regards. MoH
            +260979112233 < You have successfully registered 8 week pregnant mother with phone number +260977123456
        """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(8))
        self.assertEqual(client.gestation_at_subscription, 8)
        self.assertEqual(client.connection.identity, '+260977123456')
        self.assertEqual(client.facility, self.clinic)
        self.assertEqual(client.phone_confirmed, False)
        self.assertEqual(client.age_confirmed, False)

        # Test resubmission with same gestational period
        client.status = 'deprecated'
        client.save()
        script = """
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 0977123456
            +260979112233 < You have submitted mum's phone number +260977123456. Now reply with the mum's gestational age
            +260979112233 > 10
            +260979112233 < Mother's phone number is +260977123456 and gestational age is 10. Reply with Yes if this is correct or No if not
            +260979112233 > Yes
            +260977123456 < Welcome to the Mother Baby Service Reminder. Reply with YES if you are 10 weeks pregnant and want to receive SMS reminders about ANC. Or reply with AGE + the number of weeks if 10 is not correct. Kind regards. MoH
            +260979112233 < You have successfully registered 10 week pregnant mother with phone number +260977123456
        """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(10))
        self.assertEqual(client.gestation_at_subscription, 10)
        self.assertEqual(client.connection.identity, '+260977123456')
        self.assertEqual(client.facility, self.clinic)

        # Test resubmission with different gestational period
        client.lmp = client.lmp - timedelta(days=41 * 7)  # let previous one be old in the past
        client.save()
        script = """
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 0977123456
            +260979112233 < You have submitted mum's phone number +260977123456. Now reply with the mum's gestational age
            +260979112233 > 12
            +260979112233 < Mother's phone number is +260977123456 and gestational age is 12. Reply with Yes if this is correct or No if not
            +260979112233 > Yes
            +260977123456 < Welcome to the Mother Baby Service Reminder. Reply with YES if you are 12 weeks pregnant and want to receive SMS reminders about ANC. Or reply with AGE + the number of weeks if 12 is not correct. Kind regards. MoH
            +260979112233 < You have successfully registered 12 week pregnant mother with phone number +260977123456
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 2)
        client = Client.objects.get(pk=2)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(12))
        self.assertEqual(client.gestation_at_subscription, 12)
        self.assertEqual(client.connection.identity, '+260977123456')
        self.assertEqual(client.facility, self.clinic)

    def testRegistrationAffirmativeMotherSubmissions(self):
        self.create_chw(chw_con='+260979112233')
        script = """
            +260977123456 > age
            +260977123456 < To record your gestation age, Send AGE <GESTATIONAL-AGE IN WEEKS>, E.g. AGE 8
            +260977123456 > age 4
            +260977123456 < To register a pregnancy ask your community health worker to do it for you
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 0977123456
            +260979112233 < You have submitted mum's phone number +260977123456. Now reply with the mum's gestational age
            +260979112233 > 8
            +260979112233 < Mother's phone number is +260977123456 and gestational age is 8. Reply with Yes if this is correct or No if not
            +260979112233 > Yes
            +260977123456 < Welcome to the Mother Baby Service Reminder. Reply with YES if you are 8 weeks pregnant and want to receive SMS reminders about ANC. Or reply with AGE + the number of weeks if 8 is not correct. Kind regards. MoH
            +260979112233 < You have successfully registered 8 week pregnant mother with phone number +260977123456
            +260977123456 > Yes
            +260977123456 < 8 antenatal clinic visits are recommended. Your first visit should be before 16 weeks. Ask for iron and folic acid tablets. To stop messages please dial 5555
        """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(8))
        self.assertEqual(client.gestation_at_subscription, 8)
        self.assertEqual(client.connection.identity, '+260977123456')
        self.assertEqual(client.facility, self.clinic)
        self.assertEqual(client.phone_confirmed, True)

        # Test resubmission with same gestational period
        # client.status = 'deprecated'
        # client.save()
        script = """
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 0977123456
            +260979112233 < You have submitted mum's phone number +260977123456. Now reply with the mum's gestational age
            +260979112233 > 10
            +260979112233 < Mother's phone number is +260977123456 and gestational age is 10. Reply with Yes if this is correct or No if not
            +260979112233 > Yes
            +260977123456 < Welcome to the Mother Baby Service Reminder. Reply with YES if you are 10 weeks pregnant and want to receive SMS reminders about ANC. Or reply with AGE + the number of weeks if 10 is not correct. Kind regards. MoH
            +260979112233 < You have successfully registered 10 week pregnant mother with phone number +260977123456
            +260977123456 > age
            +260977123456 < To record your gestation age, Send AGE <GESTATIONAL-AGE IN WEEKS>, E.g. AGE 8
            +260977123456 > age 18
            +260977123456 < 8 antenatal clinic visits are recommended. Your first visit should be before 16 weeks. Ask for iron and folic acid tablets. To stop messages please dial 5555
        """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.status, 'pregnant')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(18))
        self.assertEqual(client.gestation_at_subscription, 18)
        self.assertEqual(client.connection.identity, '+260977123456')
        self.assertEqual(client.facility, self.clinic)
        self.assertEqual(client.phone_confirmed, True)
        self.assertEqual(client.age_confirmed, True)

    def testANCRegistrationMotherRefuse(self):
        self.create_chw(chw_con='+260979112233')
        script = """
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 0977123456
            +260979112233 < You have submitted mum's phone number +260977123456. Now reply with the mum's gestational age
            +260979112233 > 8
            +260979112233 < Mother's phone number is +260977123456 and gestational age is 8. Reply with Yes if this is correct or No if not
            +260979112233 > Yes
            +260977123456 < Welcome to the Mother Baby Service Reminder. Reply with YES if you are 8 weeks pregnant and want to receive SMS reminders about ANC. Or reply with AGE + the number of weeks if 8 is not correct. Kind regards. MoH
            +260979112233 < You have successfully registered 8 week pregnant mother with phone number +260977123456
            +260977123456 > No
            +260977123456 < Thank you.
        """
        #TODO: Should numbers be flagged/blacklisted. Should CHW be informed of negative response
        # Or perhaps we should tell people the number of CHW who registered them so they can follow up
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 1)
        client = Client.objects.get(pk=1)
        self.assertEqual(client.status, 'refused')
        self.assertTrue(client.lmp != None)
        self.assertEqual(client.lmp, Client.find_lmp(8))
        self.assertEqual(client.gestation_at_subscription, 8)
        self.assertEqual(client.connection.identity, '+260977123456')
        self.assertEqual(client.facility, self.clinic)
        self.assertEqual(client.phone_confirmed, False)
        self.assertEqual(client.is_active, False)

    def testNegativeGestationAge(self):
        self.create_chw(chw_con='+260979112233')
        script = """
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 0977123456
            +260979112233 < You have submitted mum's phone number +260977123456. Now reply with the mum's gestational age
            +260979112233 > -12
            +260979112233 < Mother's phone number is +260977123456 and gestational age is 12. Reply with Yes if this is correct or No if not
            +260979112233 > Yes
            +260977123456 < Welcome to the Mother Baby Service Reminder. Reply with YES if you are 12 weeks pregnant and want to receive SMS reminders about ANC. Or reply with AGE + the number of weeks if 12 is not correct. Kind regards. MoH
            +260979112233 < You have successfully registered 12 week pregnant mother with phone number +260977123456
            """
        self.runScript(script)
        self.receiveAllMessages()

    def testANCRegistrationErrorHandling(self):
        self.create_chw(chw_con='+260979112233')
        script = """
            +260979112233 > ANC
            +260979112233 < Hi Donald Clinton, to register a pregnancy first reply with mother's Airtel or MTN phone number
            +260979112233 > 097712345x
            +260979112233 < Sorry 097712345x is not a valid Airtel or MTN number. Reply with correct number
            +260979112233 > 09771234566
            +260979112233 < Sorry 09771234566 is not a valid Airtel or MTN number. Reply with correct number
            +260979112233 > 097712345
            +260979112233 < Sorry 097712345 is not a valid Airtel or MTN number. Reply with correct number
            +260979112233 > 77123456
            +260979112233 < Sorry 77123456 is not a valid Airtel or MTN number. Reply with correct number
            +260979112233 > 971234560
            +260979112233 < You have submitted mum's phone number +260971234560. Now reply with the mum's gestational age
            +260979112233 > 971234560
            +260979112233 < Sorry 971234560 gestational age is too much. You cannot register a mother's pregnancy when gestational age is already 40 or above
            +260979112233 > 40
            +260979112233 < Sorry you cannot register a mother's pregnancy when gestational age is already 40 or above
            +260979112233 > 1x2 weeks
            +260979112233 < Sorry 1x2 weeks is not a valid gestational age. Enter a valid number
            +260979112233 > 39 weeks
            +260979112233 < Mother's phone number is +260971234560 and gestational age is 39. Reply with Yes if this is correct or No if not
            +260979112233 > No
            +260979112233 < You can start a new submission by sending ANC
            """
        self.runScript(script)
        self.assertEqual(Client.objects.all().count(), 0)

    def testSendANCMessagesClientOnly(self):
        self.create_educational_messages()
        gestational_ages = [item[0] for item in EDUCATIONAL_MESSAGES]
        self.assertEqual(Client.objects.count(), 0)
        for age in gestational_ages:
            if age >= 40:  # get around validation
                backend = Connection.objects.get(pk=1).backend
                conn, _ = Connection.objects.get_or_create(identity="client%s" % age, backend=backend)

                Client.objects.get_or_create(gestation_at_subscription=age,
                                             lmp=Client.find_lmp(age), facility=self.clinic,
                                             connection=conn, phone_confirmed=True)
                # self.create_client(client_con="client%s" % age, gestational_age=age-40)
                # client = Client.objects.get(connection__identity="client%s" % age, gestation_at_subscription=age-40)
                # client.lmp = Client.find_lmp(age)
                # client.gestation_at_subscription = age
                # client.save()
            else:
                # TODO: fix this method
                self.create_client(client_con=("client%s" % age), gestational_age=age)

        self.assertEqual(SentClientMessage.objects.count(), 0)

        time.sleep(.2)
        # start router and send a notification
        self.startRouter()
        tasks.send_anc_messages(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(SentClientMessage.objects.count(), len(gestational_ages))

        for item in EDUCATIONAL_MESSAGES:
            self.assertTrue(SentClientMessage.objects.filter(client__connection__identity="client%s" % item[0],
                                                             message__text=item[1]).exists(), 'Not found %s' % item[1])

    def testSendANCMessagesClientAndCHW(self):
        self.create_educational_messages()
        gestational_ages = [item[0] for item in EDUCATIONAL_MESSAGES]
        self.assertEqual(Client.objects.count(), 0)
        chw = self.create_chw()
        for age in gestational_ages:
            if age >= 40:  # get around validation
                backend = Connection.objects.get(pk=1).backend
                conn, _ = Connection.objects.get_or_create(identity="client%s" % age, backend=backend)

                Client.objects.get_or_create(gestation_at_subscription=age,
                                             lmp=Client.find_lmp(age), facility=self.clinic,
                                             connection=conn, phone_confirmed=True, community_worker=chw)
            else:
                self.create_client(client_con=("client%s" % age), gestational_age=age, community_worker=chw)

        self.assertEqual(SentClientMessage.objects.count(), 0)

        time.sleep(.2)
        # start router and send a notification
        self.startRouter()
        tasks.send_anc_messages(self.router)

        # Get all the messages sent
        msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(SentClientMessage.objects.count(), len(gestational_ages))
        self.assertEqual(SentCHWMessage.objects.count(), len(gestational_ages))

        self.assertTrue(SentCHWMessage.objects.all()[0].message == SentClientMessage.objects.all()[0].message)

        for item in EDUCATIONAL_MESSAGES:
            self.assertTrue(SentClientMessage.objects.filter(client__connection__identity="client%s" % item[0],
                                                             message__text=item[1]).exists(), 'Not found %s' % item[1])

    def testSendANCMessagesCHWOnly(self):
        self.create_educational_messages()
        gestational_ages = [item[0] for item in EDUCATIONAL_MESSAGES]
        self.assertEqual(Client.objects.count(), 0)
        chw = self.create_chw()
        for age in gestational_ages:
            if age >= 40:  # get around validation
                backend = Connection.objects.get(pk=1).backend
                conn, _ = Connection.objects.get_or_create(identity="client%s" % age, backend=backend)

                Client.objects.get_or_create(gestation_at_subscription=age,
                                             lmp=Client.find_lmp(age), facility=self.clinic,
                                             connection=conn, community_worker=chw)
            else:
                client = self.create_client(client_con=("client%s" % age), gestational_age=age, community_worker=chw)
                client.phone_confirmed = False
                client.save()

        self.assertEqual(SentClientMessage.objects.count(), 0)

        time.sleep(.2)
        # start router and send a notification
        self.startRouter()
        tasks.send_anc_messages(self.router)

        # Get all the messages sent
        # msgs = self.receiveAllMessages()
        self.stopRouter()

        self.assertEqual(SentClientMessage.objects.count(), 0)
        self.assertEqual(SentCHWMessage.objects.count(), len(gestational_ages))
        self.assertEqual(SentCHWMessage.objects.filter(community_worker=chw).count(), len(gestational_ages))
        self.assertEqual(Message.objects.filter(direction='O', connection=chw.connection).count(), 4 + len(gestational_ages))
        self.assertEqual(Message.objects.filter(direction='O', connection=chw.connection, text__istartswith='client').count(), len(gestational_ages))


        for item in EDUCATIONAL_MESSAGES:
            chw_msg = item[1].replace(' Stop messages with 5555', '')
            self.assertTrue(Message.objects.filter(connection=chw.connection,
                                                   text__endswith="%s: %s" % ("client%s" % item[0], chw_msg)).exists(),
                            'Not found %s' % "%s: %s" % (client.connection.identity, chw_msg))

    def testSendANCMessagesCHWOnlyClientInactive(self):
        self.create_educational_messages()
        gestational_ages = [item[0] for item in EDUCATIONAL_MESSAGES]
        self.assertEqual(Client.objects.count(), 0)
        chw = self.create_chw()
        for age in gestational_ages:
            if age >= 40:  # get around validation
                backend = Connection.objects.get(pk=1).backend
                conn, _ = Connection.objects.get_or_create(identity="client%s" % age, backend=backend)

                Client.objects.get_or_create(gestation_at_subscription=age,
                                             lmp=Client.find_lmp(age), facility=self.clinic,
                                             connection=conn, community_worker=chw, phone_confirmed=True,
                                             is_active=False)
            else:
                client = self.create_client(client_con=("client%s" % age), gestational_age=age, community_worker=chw)
                client.is_active = False
                client.save()

        self.assertEqual(SentClientMessage.objects.count(), 0)

        time.sleep(.2)
        # start router and send a notification
        self.startRouter()
        tasks.send_anc_messages(self.router)

        self.stopRouter()

        self.assertEqual(SentClientMessage.objects.count(), 0)
        self.assertEqual(SentCHWMessage.objects.count(), len(gestational_ages))

        for item in EDUCATIONAL_MESSAGES:
            chw_msg = item[1].replace(' Stop messages with 5555', '')
            self.assertTrue(Message.objects.filter(connection=chw.connection,
                                                   text__endswith="%s: %s" % ("client%s" % item[0], chw_msg)).exists(),
                            'Not found %s' % "%s: %s" % (client.connection.identity, chw_msg))

    def testStatusMessage(self):
        self.create_client()
        client = Client.objects.get()
        client.status = ''
        # run task
        script = """
            client > Thank you
            client < Sorry, the system could not understand your message. For emergencies contact your local clinic
        """
        self.runScript(script)

    def testIgnoreHandleInvalidMessage(self):
        self.create_client()
        script = """
            client > Thank you
            client < Sorry, the system could not understand your message. For emergencies contact your local clinic
        """
        self.runScript(script)


    def testUnsubscribing(self):
        script = """
            client > 555555
            client < Thank you for your submission to stop receiving messages
        """
        self.runScript(script)
        self.assertEqual(WaitingForResponse.objects.all().count(), 0)

        self.create_client()
        script = """
            client > 555555 
            client > 1            
        """

        # received = "client < You have successfully unsubscribed. Please let us know why. Send 1 for Pregnancy ended\n2 for Baby was still-born\n3 for Do not want reminders"

        self.runScript(script)

        self.assertEqual(WaitingForResponse.objects.all().count(), 1)
        self.assertEqual(Client.objects.get(pk=1).status, 'miscarriage')
        self.assertEqual(Client.objects.get(pk=1).is_active, False)
        # TODO test messages received

        self.create_client('client2')
        script = """
            client2 > 555555 
            client2 > 2            
        """
        self.runScript(script)

        self.assertEqual(WaitingForResponse.objects.filter(response=None).count(), 0)
        self.assertEqual(Client.objects.get(connection__identity='client2').status, 'stillbirth')
        self.assertEqual(Client.objects.get(connection__identity='client2').is_active, False)
        # TODO test messages received

        self.create_client('client3')
        script = """
            client3 > 555555 
            client3 > 42            
        """
        self.runScript(script)

        self.assertEqual(Client.objects.get(connection__identity='client3').status, 'stop')
        self.assertEqual(Client.objects.get(connection__identity='client3').is_active, False)
        # TODO test messages received
