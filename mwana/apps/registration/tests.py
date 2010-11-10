"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from mwana import const
from rapidsms.contrib.handlers.app import App as handler_app
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.stringcleaning.app import App as cleaner_App


class TestApp(TestScript):
#    apps = (cleaner_App, handler_app, )
    
    def testRegistration(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)
        script = """
            lost   > join
            lost   < To register, send JOIN <LOCATION CODE> <NAME> <SECURITY CODE>
            rb     > join kdh rupiah banda 123q
            rb     < Sorry, 123q wasn't a valid security code. Please make sure your code is a 4-digit number like 1234. Send JOIN <LOCATION CODE> <YOUR NAME> <SECURITY CODE>.
            tk     > join kdh tizie kays -1000
            tk     < Hi Tizie Kays, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            jk     > join kdh jordan katembula -1000
            jk     < Hi Jordan Katembula, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            rb     > join kdh rupiah banda1000
            rb     < Sorry, you should put a space before your pin. Please make sure your code is a 4-digit number like 1234. Send JOIN <LOCATION CODE> <YOUR NAME> <SECURITY CODE>.
            rb     > join kdh rupiah banda 2001234
            rb     < Sorry, 2001234 wasn't a valid security code. Please make sure your code is a 4-digit number like 1234. Send JOIN <LOCATION CODE> <YOUR NAME> <SECURITY CODE>.
            rb     > join kdh rupiah banda4004444
            rb     < Sorry, you should put a space before your pin. Please make sure your code is a 4-digit number like 1234. Send JOIN <LOCATION CODE> <YOUR NAME> <SECURITY CODE>.
            rb     > join kdh rupiah banda 1234
            rb     < Hi Rupiah Banda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            ts     > join 403012 li  1234
            ts     < Hi Li, thanks for registering for Results160 from Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kk     > join whoops kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code whoops. Please check your code and try again.
            noname > join abc
            noname < Sorry, I didn't understand that. Make sure you send your location, name and pin like: JOIN <LOCATION CODE> <NAME> <SECURITY CODE>.
            tooshortname > join kdh j 1234
            tooshortname < Sorry, you must provide a valid name to register. To register, send JOIN <LOCATION CODE> <NAME> <SECURITY CODE>
        """
        self.runScript(script)
        self.assertEqual(4, Contact.objects.count(), "Registration didn't create a new contact!")
        rb = Contact.objects.get(name = "Rupiah Banda")
        self.assertEqual(kdh, rb.location, "Location was not set correctly after registration!")
        self.assertEqual(rb.types.count(), 1)
        self.assertEqual(rb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)


        script = """
            jb     > join 4o30i2 jacob banda 1234
            jb     < Hi Jacob Banda, thanks for registering for Results160 from Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kk     > join 4f30i2 kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code 4f3012. Please check your code and try again.
        """
        self.runScript(script)
        self.assertEqual(5, Contact.objects.count())
        jb = Contact.objects.get(name='Jacob Banda')
        self.assertEqual(central_clinic, jb.location)
        self.assertEqual(jb.types.count(), 1)
        self.assertEqual(jb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)
    
    def testAgentThenJoinRegistrationSameClinic(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        # the same clinic
        script = """
            rb     > agent kdh 02 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.
            rb     > join kdh rupiah banda -1000
            rb     < Hi Rupiah Banda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
        """
        self.runScript(script)
    
    def testAgentThenJoinRegistrationDifferentClinics(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="404040", type=ctr)
        # different clinics
        script = """
            rb     > agent 404040 02 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Central Clinic.
            rb     > join kdh rupiah banda -1000
            rb     < Your phone is already registered to Rupiah Banda at Central Clinic. To change name or location first reply with keyword 'LEAVE' and try again.
        """
        self.runScript(script)

    def testJoinThenAgentRegistrationSameClinic(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        # the same clinic
        script = """
            rb     > join kdh rupiah banda -1000
            rb     < Hi Rupiah Banda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            rb     > agent kdh 02 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.
        """
        self.runScript(script)

    def testJoinThenAgentRegistrationDifferentClinics(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="101010", type=ctr)
        # different clinics
        script = """
            rb     > join 101010 rupiah banda -1000
            rb     < Hi Rupiah Banda, thanks for registering for Results160 from Central Clinic. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            rb     > agent kdh 02 rupiah banda
            rb     < Hello Rupiah Banda! You are already registered as a RemindMi Agent for Central Clinic. To leave your current clinic and join Kafue District Hospital, reply with LEAVE and then re-send your message.
        """
        self.runScript(script)

    def testCbaDeregistration(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        Location.objects.create(name="Kafue District Hospital",
                                      slug="202020", type=ctr)
        Location.objects.create(name="Central Clinic",
                                                 slug="101010", type=ctr)
        # create support contacts
        script = """
            +260979565991     > join 202020 support 1 1000
            +260979565991     < Hi Support 1, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565992     > join 202020 support 2 1000
            +260979565992     < Hi Support 2, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565993     > join 202020 support 3 1000
            +260979565993     < Hi Support 3, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        admins = Contact.objects.all()
        for admin in admins:
            admin.is_help_admin = True
            admin.save()

        # create clinic workers
        script = """
            +260979565994     > join 202020 James Phiri 1000
            +260979565994     < Hi James Phiri, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565995     > join 202020 James Banda 1000
            +260979565995     < Hi James Banda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565996     > join 202020 Peter Kunda 1000
            +260979565996     < Hi Peter Kunda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)

        # create CBA's
        script = """
            +260977777751     > agent 202020 02 rupiah banda
            +260977777751     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.
            +260977777752     > agent 101010 02 rupiah banda
            +260977777752     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Central Clinic.
            +260977777753     > agent 202020 02 kunda banda
            +260977777753     < Thank you Kunda Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.
            +260977777754     > agent 202020 02 kunda banda
            +260977777754     < Thank you Kunda Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.
            +260977777755     > agent 202020 02 James Banda
            +260977777755     < Thank you James Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.
            +260977777756     > agent 202020 02 Trevor Sinkala
            +260977777756     < Thank you Trevor Sinkala! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.

            """
        self.runScript(script)

        #test deregistering by a cba
        script = """
            +260977777756 > deregister James Banda
            +260977777756 < Sorry, you are NOT allowed to deregister anyone. If you think this message is a mistake reply with keyword HELP
        """
        self.runScript(script)

        #test deregistering fellow clinic worker
        script = """
            +260979565994 > deregister Peter Kunda
            +260979565994 < The name Peter Kunda does not belong to any CBA at Kafue District Hospital. Make sure you typed it correctly
            +260979565994 > deregister 260979565996
            +260979565994 < The phone number 260979565996 does not belong to any CBA at Kafue District Hospital. Make sure you typed it correctly
        """
        self.runScript(script)

        #test deregistering cba whose name(or name part) is common to too many people
        script = """
            +260979565994 > deregister a
            +260979565994 < There are 5 CBA's who's names match a at Kafue District Hospital. Try to use the phone number instead
            """
        self.runScript(script)

        #test deregistering cba whose name is not unique at same clinic
        script = """
            +260979565994 > deregister Kunda Banda
            +260979565994 < Try sending REMOVE <CBA_PHONE_NUMBER>. Which CBA did you mean? Kunda Banda:+260977777753 or Kunda Banda:+260977777754
            +260979565994 > deregister +260977777754
            +260979565991 < James Phiri:+260979565994 has deregistered Kunda Banda:+260977777754 of zone 02 at Kafue District Hospital
            +260979565992 < James Phiri:+260979565994 has deregistered Kunda Banda:+260977777754 of zone 02 at Kafue District Hospital
            +260979565993 < James Phiri:+260979565994 has deregistered Kunda Banda:+260977777754 of zone 02 at Kafue District Hospital
            +260979565994 < You have successfully deregistered Kunda Banda:+260977777754 of zone 02 at Kafue District Hospital
        """
        self.runScript(script)
        cba = Contact.objects.get(connection__identity="+260977777754")
        self.assertEqual(cba.is_active, False)

        #test deregistering cba whose name is not unique in system but at clinic
        script = """
            +260979565996 > deregister rupiah BandA
            +260979565991 < Peter Kunda:+260979565996 has deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
            +260979565992 < Peter Kunda:+260979565996 has deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
            +260979565993 < Peter Kunda:+260979565996 has deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
            +260979565996 < You have successfully deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
        """
        self.runScript(script)
        cba = Contact.objects.get(connection__identity="+260977777751")
        self.assertEqual(cba.is_active, False)

        #test deregistering cba using phone number without country code
        script = """
            +260979565996 > deregister 0977777756
            +260979565991 < Peter Kunda:+260979565996 has deregistered Trevor Sinkala:+260977777756 of zone 02 at Kafue District Hospital
            +260979565992 < Peter Kunda:+260979565996 has deregistered Trevor Sinkala:+260977777756 of zone 02 at Kafue District Hospital
            +260979565993 < Peter Kunda:+260979565996 has deregistered Trevor Sinkala:+260977777756 of zone 02 at Kafue District Hospital
            +260979565996 < You have successfully deregistered Trevor Sinkala:+260977777756 of zone 02 at Kafue District Hospital
        """
        self.runScript(script)
        cba = Contact.objects.get(connection__identity="+260977777756")
        self.assertEqual(cba.is_active, False)
       