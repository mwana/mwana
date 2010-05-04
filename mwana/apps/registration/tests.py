"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from mwana import const
from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.stringcleaning.app import App as cleaner_App


class TestApp(TestScript):
    apps = (cleaner_App, handler_app, )
    
    def testRegistration(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)
        script = """
            lost   > join
            lost   < To register, send JOIN <CLINIC CODE> <NAME> <SECURITY CODE>
            rb     > join kdh rupiah banda 123q
            rb     < Sorry, 123q wasn't a valid security code. Please make sure your code is a 4-digit number like 1234. Send JOIN <CLINIC CODE> <YOUR NAME> <SECURITY CODE>.
            tk     > join kdh tizie kays -1000
            tk     < Hi Tizie Kays, thanks for registering for DBS results from Results160 as staff of Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if your information is not correct.
            jk     > join kdh jordan katembula -1000
            jk     < Hi Jordan Katembula, thanks for registering for DBS results from Results160 as staff of Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if your information is not correct.
            rb     > join kdh rupiah banda1000
            rb     < Sorry, you should put a space before your pin. Please make sure your code is a 4-digit number like 1234. Send JOIN <CLINIC CODE> <YOUR NAME> <SECURITY CODE>.
            rb     > join kdh rupiah banda 2001234
            rb     < Sorry, 2001234 wasn't a valid security code. Please make sure your code is a 4-digit number like 1234. Send JOIN <CLINIC CODE> <YOUR NAME> <SECURITY CODE>.
            rb     > join kdh rupiah banda4004444
            rb     < Sorry, you should put a space before your pin. Please make sure your code is a 4-digit number like 1234. Send JOIN <CLINIC CODE> <YOUR NAME> <SECURITY CODE>.
            rb     > join kdh rupiah banda 1234
            rb     < Hi Rupiah Banda, thanks for registering for DBS results from Results160 as staff of Kafue District Hospital. Your PIN is 1234. Reply with keyword 'HELP' if your information is not correct.
            kk     > join whoops kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code whoops. Please check your code and try again.
            noname > join abc
            noname < Sorry, I didn't understand that. Make sure you send your location, name and pin like: JOIN <CLINIC CODE> <NAME> <SECURITY CODE>.
        """
        self.runScript(script)
        self.assertEqual(3, Contact.objects.count(), "Registration didn't create a new contact!")
        rb = Contact.objects.get(name = "Rupiah Banda")
        self.assertEqual(kdh, rb.location, "Location was not set correctly after registration!")
        self.assertEqual(rb.types.count(), 1)
        self.assertEqual(rb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)


        script = """
            jb     > join 4o30i2 jacob banda 1234
            jb     < Hi Jacob Banda, thanks for registering for DBS results from Results160 as staff of Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if your information is not correct.
            kk     > join 4f30i2 kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code 4f3012. Please check your code and try again.
        """
        self.runScript(script)
        self.assertEqual(4, Contact.objects.count())
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
            rb     < Hi Rupiah Banda, thanks for registering for DBS results from Results160 as staff of Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if your information is not correct.
        """
        self.runScript(script)
    
    def testAgentThenJoinRegistrationDifferentClinics(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="central", type=ctr)
        # different clinics
        script = """
            rb     > agent central 02 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Central Clinic.
            rb     > join kdh rupiah banda -1000
            rb     < Your phone is already registered to Rupiah Banda at Central Clinic. To change name or clinic first reply with keyword 'LEAVE' and try again.
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
            rb     < Hi Rupiah Banda, thanks for registering for DBS results from Results160 as staff of Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if your information is not correct.
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
                                                 slug="central", type=ctr)
        # different clinics
        script = """
            rb     > join central rupiah banda -1000
            rb     < Hi Rupiah Banda, thanks for registering for DBS results from Results160 as staff of Central Clinic. Your PIN is 1000. Reply with keyword 'HELP' if your information is not correct.
            rb     > agent kdh 02 rupiah banda
            rb     < Hello Rupiah Banda! You are already registered as a RemindMi Agent for Central Clinic. To leave your current clinic and join Kafue District Hospital, reply with LEAVE and then re-send your message.
        """
        self.runScript(script)