# vim: ai ts=4 sts=4 et sw=4

#TODO : add tests to carter for the modification to notify hub workers and dho's

from mwana.apps.training.models import Trained
from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from rapidsms.models import Contact
from mwana.apps.training import tasks
from mwana.apps.training.models import TrainingSession
import time


class TestApp(TestScript):
    def setUp(self):
        super(TestApp, self).setUp()
        self.assertEqual(0, Contact.objects.count())
        dist_type = LocationType.objects.create(slug=const.DISTRICT_SLUGS[0])
        district = Location.objects.create(name="Kafue District",
                                      slug="kd", type=dist_type)
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr, parent=district)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012",
                                                 type=ctr, parent=district)
        # register trainer with some facility
        script = """
            tz > join kdh trainer zulu 1234
            tz < Hi Trainer Zulu, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)

        # create support staff
        script = """
            ha > join kdh Helper Phiri 1111
            ha < Hi Helper Phiri, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1111. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        help_admin=Contact.objects.get(connection__identity='ha')
        help_admin.is_help_admin = True
        help_admin.save()

        # create hub workers
        script = """
            hub_worker > join hub kdh Hub Man 1111
            hub_worker < Hi Hub Man, thanks for registering for Results160 from hub at Kafue District Hospital. Your PIN is 1111. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        help_admin=Contact.objects.get(connection__identity='ha')
        help_admin.is_help_admin = True
        help_admin.save()

    def testTrainingNotification(self):

        # Incomplete command
        script = """
            tz > training start
            tz < To send notification for starting a training , send TRAINING START <CLINIC CODE>
            tz > training stop
            tz < To send notification for stopping a training , send TRAINING STOP <CLINIC CODE>
            """
        self.runScript(script)

        # unknown location
        script = """
            tz > training start java
            tz < Sorry, I don't know about a location with code java. Please check your code and try again.
            tz > training stop java
            tz < Sorry, I don't know about a location with code java. Please check your code and try again.
            """
        self.runScript(script)

        # at start of training
        script = """
            tz > training start kdh
            ha < Training is starting at Kafue District Hospital, kdh. Notification was sent by Trainer Zulu, tz
            hub_worker < Hi Hub Man. Training is starting at Kafue District Hospital, kdh. Treat notifications you receive from this clinic as training data
            tz < Thanks Trainer Zulu for your message that training is starting for Kafue District Hospital. At end of training please send TRAINING STOP kdh
            tz < When the trainees finish the course tell them to state that they have been trained. Let each one send TRAINED <TRAINER GROUP> <USER TYPE>, E.g Trained zpct cba
            """
        self.runScript(script)

        # at end of training. scenario one - ideal flow
        script = """
            tz > training stop kdh
            ha < Training has stopped at Kafue District Hospital, kdh. Notification was sent by Trainer Zulu, tz            
            hub_worker < Hi Hub Man. Training has stopped at Kafue District Hospital, kdh. Treat notifications you receive from this clinic as live data
            tz < Thanks Trainer Zulu for your message that training has stopped for Kafue District Hospital.
            """
        self.runScript(script)

        # at end of training. scenario two. trainer forgot to send training stop
        # start training for central clinic
        script = """
            tz > training start 403012
            ha < Training is starting at Central Clinic, 403012. Notification was sent by Trainer Zulu, tz
            hub_worker < Hi Hub Man. Training is starting at Central Clinic, 403012. Treat notifications you receive from this clinic as training data
            tz < Thanks Trainer Zulu for your message that training is starting for Central Clinic. At end of training please send TRAINING STOP 403012
            tz < When the trainees finish the course tell them to state that they have been trained. Let each one send TRAINED <TRAINER GROUP> <USER TYPE>, E.g Trained zpct cba
            """
        self.runScript(script)
        time.sleep(0.1)
        self.startRouter()
        self.assertEqual(1, TrainingSession.objects.filter(is_on=True).count())
#        self.startRouter()
        #manually call scheduled task
        tasks.send_endof_training_notification(self.router)

        msgs = self.receiveAllMessages()
        self.stopRouter()
        
        trainer_msg = "Hi Trainer Zulu, please send TRAINING STOP if you have stopped training for today at Central Clinic"
        admin_msg ="A reminder was sent to Trainer Zulu, tz to state if training has ended for Central Clinic, 403012"

        self.assertEqual(msgs[-1].text,admin_msg)
        self.assertEqual(msgs[-2].text,trainer_msg)
        self.assertEqual(msgs[-1].connection.identity,"ha")
        self.assertEqual(msgs[-2].connection.identity,"tz")


        script = """
            tz > training stop 403012
            ha < Training has stopped at Central Clinic, 403012. Notification was sent by Trainer Zulu, tz
            hub_worker < Hi Hub Man. Training has stopped at Central Clinic, 403012. Treat notifications you receive from this clinic as live data
            tz < Thanks Trainer Zulu for your message that training has stopped for Central Clinic.
            """
        self.runScript(script)

        self.assertEqual(0, TrainingSession.objects.filter(is_on=True).count())

    def testTrainedRegistration(self):

        # Incomplete command
        script = """
            tz > trained unicef cba
            tz < Thanks Trainer Zulu. You have been trained as Clinic Worker at Kafue District Hospital
            tz > trained any text
            tz < Thanks Trainer Zulu. You have been trained as Clinic Worker at Kafue District Hospital
            """
        self.runScript(script)

        self.assertEqual(1, Trained.objects.all().count())
