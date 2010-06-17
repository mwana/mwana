from mwana import const
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript



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
            0974 < Contacts at Central Clinic: Help Admin;0974. ****Worker Three;0973. ****Worker Two;0972.
            0974 > contacts 403012 what ever
            0974 < Contacts at Central Clinic: Help Admin;0974. ****Worker Three;0973. ****Worker Two;0972.
            0974 > contacts 403012 0
            0974 < Contacts at Central Clinic: Help Admin;0974. ****Worker Three;0973. ****Worker Two;0972.
            0974 > contacts 403012 2
            0974 < Contacts at Central Clinic: Help Admin;0974. ****Worker Three;0973.
            0974 > contacts 403012 two
            0974 < Contacts at Central Clinic: Help Admin;0974. ****Worker Three;0973.
            0974 > contacts 403012 -1
            0974 < Contacts at Central Clinic: Help Admin;0974.
            0974 > contacts 403012 -one
            0974 < Contacts at Central Clinic: Help Admin;0974.
        """
        self.runScript(script)

