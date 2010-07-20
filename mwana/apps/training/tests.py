"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from mwana import const
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from rapidsms.models import Connection
from rapidsms.models import Contact
from mwana.apps.training import tasks
from mwana.apps.training.models import TrainingSession


class TestApp(TestScript):
    def setUp(self):
        super(TestApp, self).setUp()
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)
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
            tz < Thanks Trainer Zulu for your message that training is starting for Kafue District Hospital. At end of training please send TRAINING STOP
            """
        self.runScript(script)

        # at end of training. scenario one - ideal flow
        script = """
            tz > training stop kdh
            ha < Training has stopped at Kafue District Hospital, kdh. Notification was sent by Trainer Zulu, tz
            tz < Thanks Trainer Zulu for your message that training has stopped for Kafue District Hospital.
            """
        self.runScript(script)

        # at end of training. scenario two. trainer forgot to send training stop
        # start training for central clinic
        script = """
            tz > training start 403012
            ha < Training is starting at Central Clinic, 403012. Notification was sent by Trainer Zulu, tz
            tz < Thanks Trainer Zulu for your message that training is starting for Central Clinic. At end of training please send TRAINING STOP
            """
        self.runScript(script)

        self.assertEqual(1, TrainingSession.objects.filter(is_on=True).count())
        self.startRouter()
        #manually call scheduled task
        tasks.send_endof_training_notification(self.router)

        msgs = self.receiveAllMessages()
        trainer_msg = "Hi Trainer Zulu, please send TRAINING STOP if you have stopped training for today at Central Clinic"
        admin_msg ="A reminder was sent to Trainer Zulu, tz to state if training has ended for Central Clinic, 403012"

        self.assertEqual(msgs[-1].text,admin_msg)
        self.assertEqual(msgs[-2].text,trainer_msg)
        self.assertEqual(msgs[-1].connection.identity,"ha")
        self.assertEqual(msgs[-2].connection.identity,"tz")


        script = """
            tz > training stop 403012
            ha < Training has stopped at Central Clinic, 403012. Notification was sent by Trainer Zulu, tz
            tz < Thanks Trainer Zulu for your message that training has stopped for Central Clinic.
            """
        self.runScript(script)

        self.assertEqual(0, TrainingSession.objects.filter(is_on=True).count())
