# vim: ai ts=4 sts=4 et sw=4
import datetime
import json

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mwana import const
from mwana.apps.training.models import TrainingSession
from mwana.apps.help.models import HelpAdminGroup
from mwana.apps.help.models import HelpRequest
from mwana.apps.labresults.testdata.payloads import CHANGED_PAYLOAD
from mwana.apps.labresults.testdata.payloads import INITIAL_PAYLOAD
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import ReportingGroup

from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript


class TestApp(TestScript):
    def setUp(self):
        # this call is required if you want to override setUp
        super(TestApp, self).setUp()
        # create some contacts
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        self.kdh = Location.objects.create(name="Kafue District Hospital",
                                           slug="kdh", type=ctr)
        self.central_clinic = Location.objects.create(name="Central Clinic",
                                                      slug="403012", type=ctr)

        ghost_clinic = Location.objects.create(name="Ghost Clinic",
                                               slug="ghost", type=ctr)
        #create some contacts for the facilities
        script = """
            0971 > join kdh worker one  1234
            0972 > join 403012 worker two  1234
            0973 > join 403012 worker three  1234
            0974 > join 403012 help admin  1234
            0975 > join cba kdh 2 Kafue CBA
            0976 > join cba 403012 2 Central CBA
        """
        self.runScript(script)

        # Turn on help-admin contact
        self.help_admin = Contact.active.get(connection__identity="0974")
        self.help_admin.is_help_admin = True
        self.help_admin.save()

    def testGettingContacts(self):
        """
        Tests getting names and phone numbers for active concats at a clinic by
        HELP ADMINS
        """

    def testHelp(self):
        script = """
            unknown > help
            0974 < Someone has requested help. Please call them at unknown.
            unknown < Sorry you're having trouble. Your help request has been forwarded to a support team member and they will call you soon.
            0971 > help
            0974 < Worker One (worker) at Kafue District Hospital(kdh) has requested help. Please call them at 0971.
            0971 < Sorry you're having trouble Worker One. Your help request has been forwarded to a support team member and they will call you soon.
        """
        self.runScript(script)
        self.assertEqual(Message.objects.filter(direction='O',
                                                text__contains='requested help',
                                                contact=self.help_admin).count(), 2)
        self.assertEqual(HelpRequest.objects.count(), 2)

        # Test help admin groups
        group = ReportingGroup.objects.create(name="Mansa District")
        HelpAdminGroup.objects.create(contact=self.help_admin, group=group)
        GroupFacilityMapping.objects.create(facility=self.central_clinic, group=group)

        script = """
            0971 > help
            0971 < Sorry you're having trouble Worker One. Your help request has been forwarded to a support team member and they will call you soon.
        """
        self.runScript(script)
        self.assertEqual(Message.objects.filter(direction='O',
                                                text__contains='requested help',
                                                contact__name__iexact='help admin').count(), 2)
        self.assertEqual(HelpRequest.objects.count(), 3)

        GroupFacilityMapping.objects.create(facility=self.kdh, group=group)

        script = """
            0971 > help
            0974 < Worker One (worker) at Kafue District Hospital(kdh) has requested help. Please call them at 0971.
            0971 < Sorry you're having trouble Worker One. Your help request has been forwarded to a support team member and they will call you soon.
        """
        self.runScript(script)
        self.assertEqual(Message.objects.filter(direction='O',
                                                text__contains='requested help',
                                                contact__name__iexact='help admin').count(), 3)
        self.assertEqual(HelpRequest.objects.count(), 4)


    def testTrainingAwareHelpForwarding(self):
        # Start a training session for KDH but not central clinic
        script = """
            0974 > Training start kdh
            """
        self.runScript(script)
        self.receiveAllMessages()
        self.assertEqual(1, TrainingSession.objects.filter(location=self.kdh, is_on=True).count())


        # Total forwarded help requests will be come 1
        script = """
            unknown > help
            0974 < Someone has requested help. Please call them at unknown.
            unknown < Sorry you're having trouble. Your help request has been forwarded to a support team member and they will call you soon.
            """
        self.runScript(script)

        # Total forwarded help requests will be come 2
        script = """
            0971 > help
            0974 < Worker One (worker) at Kafue District Hospital(kdh) has requested help. Please call them at 0971.
            0971 < Sorry you're having trouble Worker One. Your help request has been forwarded to a support team member and they will call you soon.
            """
        self.runScript(script)

        # Total forwarded help requests will be come 3
        script = """
            0972 > help how to get results
            0974 < Worker Two (worker) at Central Clinic(403012) has requested help. Please call them at 0972. Their message was: how to get results
            0972 < Sorry you're having trouble Worker Two. Your help request has been forwarded to a support team member and they will call you soon.
            """
        self.runScript(script)

        # Ignore second request from this worker's location where there
        # is training. Total forwarded help requests will still be 3
        script = """
            0971 > help
            0971 < Sorry you're having trouble Worker One. Your help request has been forwarded to a support team member and they will call you soon.
            """
        self.runScript(script)

        # Forward subsequent help requests for worker location where there is
        # no training. Total forwarded help requests will be come 4
        script = """
            0972 > help how to get results
            0974 < Worker Two (worker) at Central Clinic(403012) has requested help. Please call them at 0972. Their message was: how to get results
            0972 < Sorry you're having trouble Worker Two. Your help request has been forwarded to a support team member and they will call you soon.
            """
        self.runScript(script)

        # Ignore second request from this CBA's location where there is training
        # Total forwarded help requests will still be 4
        script = """
            0975 > help
            0975 < Sorry you're having trouble Kafue Cba. Your help request has been forwarded to a support team member and they will call you soon.
            """
        self.runScript(script)

        # Forward subsequent help requests for cba location where there is no
        # training. Total forwarded help requests will be come 5

        script = """
            0976 > help postnatal
            0974 < Central Cba (cba) at Central Clinic(403012) has requested help. Please call them at 0976. Their message was: postnatal
            0976 < Sorry you're having trouble Central Cba. Your help request has been forwarded to a support team member and they will call you soon.
        """
        self.runScript(script)
        # 1 unkwon clinic, 1 at clinic with training,
        self.assertEqual(Message.objects.filter(direction='O',
                                                text__contains='requested help',
                                                contact=self.help_admin).count(), 5)
        self.assertEqual(HelpRequest.objects.count(), 7)

        # Stop the training session for KDH
        script = """
            0974 > Training stop kdh
            """
        self.runScript(script)
        self.receiveAllMessages()
        self.assertEqual(0, TrainingSession.objects.filter(location=self.kdh, is_on=True).count())

        # Help request for KDH can now be forwarded again.
        # Total forwarded help requests will be come 6
        script = """
            0971 > help
            0974 < Worker One (worker) at Kafue District Hospital(kdh) has requested help. Please call them at 0971.
            0971 < Sorry you're having trouble Worker One. Your help request has been forwarded to a support team member and they will call you soon.
            """
        self.runScript(script)

        self.assertEqual(Message.objects.filter(direction='O',
                                                text__contains='requested help',
                                                contact=self.help_admin).count(), 6)
        self.assertEqual(HelpRequest.objects.count(), 8)

    def _post_json(self, url, data):
        if not isinstance(data, basestring):
            data = json.dumps(data)
        return self.client.post(url, data, content_type='text/json')

    def testGettingPayloadReports(self):
        """
        Tests viewing number of payloads received in a time span grouped by
        source for HELP ADMINS
        """
        user = User.objects.create_user(username='adh', email='',
                                        password='abc')
        perm = Permission.objects.get(content_type__app_label='labresults',
                                      codename='add_payload')
        user.user_permissions.add(perm)
        self.client.login(username='adh', password='abc')

        # process some payloads
        payload1 = INITIAL_PAYLOAD
        payload2 = CHANGED_PAYLOAD
        self._post_json(reverse('accept_results'), payload1)
        self._post_json(reverse('accept_results'), payload2)

        payload2["source"] = payload2["source"].replace("ndola/arthur-davison", "lusaka/uth")
        self._post_json(reverse('accept_results'), payload2)

        # create some dynamic dates
        now = datetime.date.today()
        today = datetime.datetime(now.year, now.month, now.day)

        startdate1 = today - datetime.timedelta(days=7)
        enddate1 = today - datetime.timedelta(days=1 - 1) - \
                   datetime.timedelta(seconds=0.1)
        startdate2 = today - datetime.timedelta(days=8)
        enddate2 = today - datetime.timedelta(days=1 - 1) - \
                   datetime.timedelta(seconds=0.1)
        startdate3 = today - datetime.timedelta(days=7)
        enddate3 = today - datetime.timedelta(days=0 - 1) - \
                   datetime.timedelta(seconds=0.1)
        startdate4 = today
        enddate4 = today - datetime.timedelta(days=0 - 1) - \
                   datetime.timedelta(seconds=0.1)
        script = """
            unknown > payload
            unknown < To view payloads, send <PAYLOADS> <FROM-HOW-MANY-DAYS-AGO> [<TO-HOW-MANY-DAYS-AGO>], e.g PAYLOAD 7 1, (between 7 days ago and 1 day ago)
            unknown > payload
            unknown < To view payloads, send <PAYLOADS> <FROM-HOW-MANY-DAYS-AGO> [<TO-HOW-MANY-DAYS-AGO>], e.g PAYLOAD 7 1, (between 7 days ago and 1 day ago)
            unknown > paylods 7
            unknown < Sorry, you must be registered as HELP ADMIN to view payloads. If you think this message is a mistake, respond with keyword 'HELP'
            0971 > payload 7 1
            0971 < Sorry, you must be registered as HELP ADMIN to view payloads. If you think this message is a mistake, respond with keyword 'HELP'
            0974 > payload 7 1
            0974 < Period %(startdate1)s to %(enddate1)s. No payloads
            0974 > payload 8 1
            0974 < Period %(startdate2)s to %(enddate2)s. No payloads
            0974 > payload 7 0
            0974 <  PAYLOADS. Period: %(startdate3)s to %(enddate3)s. lusaka/uth;1 ****ndola/arthur-davison;2
            0974 > payload 0
            0974 <  PAYLOADS. Period: %(startdate4)s to %(enddate4)s. lusaka/uth;1 ****ndola/arthur-davison;2
            0974 > payload 0 0
            0974 <  PAYLOADS. Period: %(startdate4)s to %(enddate4)s. lusaka/uth;1 ****ndola/arthur-davison;2
            0974 > payload 0 7
            0974 <  PAYLOADS. Period: %(startdate3)s to %(enddate3)s. lusaka/uth;1 ****ndola/arthur-davison;2
            0974 > payload 0 seven
            0974 <  PAYLOADS. Period: %(startdate3)s to %(enddate3)s. lusaka/uth;1 ****ndola/arthur-davison;2
            0974 > payload seven invalid
            0974 <  PAYLOADS. Period: %(startdate3)s to %(enddate3)s. lusaka/uth;1 ****ndola/arthur-davison;2
        """ % {"startdate1": startdate1.strftime("%d/%m/%Y"), "enddate1": enddate1.strftime("%d/%m/%Y"),
               "startdate2": startdate2.strftime("%d/%m/%Y"), "enddate2": enddate2.strftime("%d/%m/%Y"),
               "startdate3": startdate3.strftime("%d/%m/%Y"), "enddate3": enddate3.strftime("%d/%m/%Y"),
               "startdate4": startdate4.strftime("%d/%m/%Y"), "enddate4": enddate4.strftime("%d/%m/%Y")}
        self.runScript(script)

    def test_getting_pin(self):
        """
        Tests getting PIN codes for a user by HELP ADMINS
        """

        script = """
            unknown > pin
            unknown < To get the PIN for a user, send PIN <PHONE_NUMBER_PATTERN>
            unknown > pin 097
            unknown < Sorry, you must be registered as HELP ADMIN to retrieve PIN codes. If you think this message is a mistake, respond with keyword 'HELP'
            0971 > pin 0972
            0971 < Sorry, you must be registered as HELP ADMIN to retrieve PIN codes. If you think this message is a mistake, respond with keyword 'HELP'
            0974 > PIN 098773
            0974 < There are no active SMS users with phone number matching 098773
            0974 > pin 0972
            0974 < Worker Two: 1234.
            0974 > pin 097
            0974 < Worker One: 1234. Worker Two: 1234. Worker Three: 1234. Help Admin: 1234.
        """
        self.runScript(script)
