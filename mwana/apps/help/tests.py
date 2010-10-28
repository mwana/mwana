import json

import datetime
import mwana.const as const
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.labresults.testdata.payloads import CHANGED_PAYLOAD, INITIAL_PAYLOAD



class TestApp(TestScript):

    def setUp(self):
        # this call is required if you want to override setUp
        super(TestApp, self).setUp()
        # create some contacts
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)

        ghost_clinic = Location.objects.create(name="Ghost Clinic",
                                                 slug="ghost", type=ctr)
        #create some contacts for the facilities
        script = """
            0971 > join kdh worker one  1234
            0972 > join 403012 worker two  1234
            0972 > agent 403012 2 worker two
            0973 > join 403012 worker three  1234
            0974 > join 403012 help admin  1234
        """
        self.runScript(script)

        # Turn on help-admin contact
        help_admin=Contact.active.get(connection__identity="0974")
        help_admin.is_help_admin=True
        help_admin.save()

    def testGettingContacts(self):
        """
        Tests getting names and phone numbers for active concats at a clinic by
        HELP ADMINS
        """

        script = """
            unknown > contacts
            unknown < To get active contacts for a clinic, send <CONTACTS> <CLINIC CODE> [<COUNT = {5}>]
            unknown > contacts kdh
            unknown < Sorry, you must be registered as HELP ADMIN to request for facility contacts. If you think this message is a mistake, respond with keyword 'HELP'
            0971 > contacts kdh
            0971 < Sorry, you must be registered as HELP ADMIN to request for facility contacts. If you think this message is a mistake, respond with keyword 'HELP'
            0974 > contacts ghost
            0974 < There are no active contacts at Ghost Clinic
            0974 > contacts kdh
            0974 < Contacts at Kafue District Hospital: Worker One;0971.
            0974 > contacts 403012
            0974 < Contacts at Central Clinic: Worker Two;0972. ****Worker Three;0973. ****Help Admin;0974.
            0974 > contacts 403012 what ever
            0974 < Contacts at Central Clinic: Worker Two;0972. ****Worker Three;0973. ****Help Admin;0974.
            0974 > contacts 403012 0
            0974 < Contacts at Central Clinic: Worker Two;0972. ****Worker Three;0973. ****Help Admin;0974.
            0974 > contacts 403012 2
            0974 < Contacts at Central Clinic: Worker Two;0972. ****Worker Three;0973.
            0974 > contacts 403012 two
            0974 < Contacts at Central Clinic: Worker Two;0972. ****Worker Three;0973.
            0974 > contacts 403012 -1
            0974 < Contacts at Central Clinic: Worker Two;0972.
            0974 > contacts 403012 -one
            0974 < Contacts at Central Clinic: Worker Two;0972.
        """
        self.runScript(script)
        
    def _post_json(self, url, data):
        if not isinstance(data, basestring):
            data = json.dumps(data)
        return self.client.post(url, data, content_type='text/json')

    def testGettingPayloadReports(self):
        """
        Tests viewing number of payloads received in a timespan grouped by
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

