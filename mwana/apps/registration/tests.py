# vim: ai ts=4 sts=4 et sw=4

import time

from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message


class TestApp(TestScript):
#    apps = (cleaner_App, handler_app, )
    
    def testCBARegistrationWithLanguage(self):
        #TODO implement test in such a way that is passes in both malawi and zambia
        pass
#        self.assertEqual(0, Contact.objects.count())
#        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
#        Location.objects.create(name="Central Clinic",
#                                                 slug="403012", type=ctr)
#
#        script = """
#            cba > join cba NYA 403012 3 rupiah banda
#            cba   < Zikomo Rupiah Banda! Mwakwanitsa kulembetsa ngati wothandiza wa RemindMi wa  3 la Central Clinic
#            phiri > join cba eng 403012 3 phiri banda
#            phiri < Thank you Phiri Banda! You have successfully registered as a RemindMi Agent for zone 3 of Central Clinic.
#        """
#        self.runScript(script)
#
#        self.assertEquals(Contact.active.filter(language='nya').count(), 1)
#        self.assertEquals(Contact.active.filter(language='').count(), 1)
#        self.assertEquals(Contact.active.all().count(), 2)

    
    def testRegistration(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        dst = LocationType.objects.create(slug=const.DISTRICT_SLUGS[0])
        prv = LocationType.objects.create(slug=const.PROVINCE_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)
        mansa = Location.objects.create(name="Mansa",
                                        slug="403000", type=dst)
        luapula = Location.objects.create(name="Luapula",
                                          slug="400000", type=prv)
        script = """
            lost   > join
            lost   < Send HELP REGISTRATION if you need to be assisted
            rb     > join clinic kdh rupiah banda 123q
            rb     < Sorry, 123q wasn't a valid pin code. Please make sure your code is a 4-digit number like 1234. Send HELP REGISTRATION if you need to be assisted
            tk     > join clinic kdh tizie kays -1000
            tk     < Hi Tizie Kays, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            jk     > join clinic kdh jordan katembula -1000
            jk     < Hi Jordan Katembula, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            rb     > join clinic kdh rupiah banda1000
            rb     < Sorry, you should put a space before your pin. Please make sure your code is a 4-digit number like 1234. Send HELP REGISTRATION if you need to be assisted
            rb     > join clinic kdh rupiah banda 2001234
            rb     < Sorry, 2001234 wasn't a valid pin code. Please make sure your code is a 4-digit number like 1234. Send HELP REGISTRATION if you need to be assisted
            rb     > join clinic kdh rupiah banda4004444
            rb     < Sorry, you should put a space before your pin. Please make sure your code is a 4-digit number like 1234. Send HELP REGISTRATION if you need to be assisted
            rb     > join clinic kdh rupiah banda 1234
            rb     < Hi Rupiah Banda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            ts     > join clinic 403012 li  1234
            ts     < Hi Li, thanks for registering for Results160 from Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kk     > join clinic whoops kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code whoops. Please check your code and try again.
            noname > join abc
            noname < Sorry, I didn't understand that. Send HELP REGISTRATION if you need to be assisted
            tooshortname > join clinic kdh j 1234
            tooshortname < Sorry, you must provide a valid name to register. Send HELP REGISTRATION if you need to be assisted
        """
        self.runScript(script)
        time.sleep(1)
        self.assertEqual(4, Contact.objects.count(), "Registration didn't create a new contact!")
        rb = Contact.objects.get(name="Rupiah Banda")
        self.assertEqual(kdh, rb.location, "Location was not set correctly after registration!")
        self.assertEqual(rb.types.count(), 1)
        self.assertEqual(rb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)
        


        script = """
            jb     > join clinic 4o30i2 jacob banda 1234
            jb     < Hi Jacob Banda, thanks for registering for Results160 from Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kk     > join clinic 4f30i2 kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code 4f3012. Please check your code and try again.
        """
        self.runScript(script)
        time.sleep(1)
        self.assertEqual(5, Contact.objects.count())
        jb = Contact.objects.get(name='Jacob Banda')
        self.assertEqual(central_clinic, jb.location)
        self.assertEqual(jb.types.count(), 1)
        self.assertEqual(jb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)

        script = """
            hubman     > join hub 4o30i2 hubman banda 1234
            hubman     < Hi Hubman Banda, thanks for registering for Results160 from hub at Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        time.sleep(.5)
        self.assertEqual(6, Contact.objects.count())
        hubman = Contact.objects.get(name='Hubman Banda')
        self.assertEqual(hubman.types.all()[0].slug, const.HUB_WORKER_SLUG)

        script = """
            dho     > join dho 4030 Dho banda 1234
            dho     < Hi Dho Banda, thanks for registering for Results160 from Mansa DHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        time.sleep(.5)
        self.assertEqual(7, Contact.objects.count())
        dho = Contact.objects.get(name='Dho Banda')
        self.assertEqual(dho.types.all()[0].slug, const.DISTRICT_WORKER_SLUG)
    
        script = """
            pho     > join pho 40 Pho banda 1234
            pho     < Hi Pho Banda, thanks for registering for Results160 from Luapula PHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        time.sleep(.5)
        self.assertEqual(8, Contact.objects.count())
        pho = Contact.objects.get(name='Pho Banda')
        self.assertEqual(pho.types.all()[0].slug, const.PROVINCE_WORKER_SLUG)

        script = """
            labman     > join lab 4o30i2 mark zuckerberg 1234
            labman     < Hi Mark Zuckerberg, thanks for registering for Results160 from lab at Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        time.sleep(.5)
        self.assertEqual(9, Contact.objects.count())
        labman = Contact.objects.get(name='Mark Zuckerberg')
        self.assertEqual(labman.types.all()[0].slug, const.LAB_WORKER_SLUG)

        script = """
            phia     > join phia 403012 broken hill 2345
            phia     < Hi Broken Hill, thanks for registering for Results160 PHIA at Central Clinic. Your PIN is 2345. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        time.sleep(.5)
        self.assertEqual(10, Contact.objects.count())
        phiaman = Contact.objects.get(name='Broken Hill')
        self.assertEqual(phiaman.types.all()[0].slug, const.PHIA_WORKER_SLUG)
        #todo: allow to clinic workers to join as phia


    def testAgentThenJoinRegistrationSameClinic(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        # the same clinic
        script = """
            rb     > join agent kdh 02 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital.
            rb     > join clinic kdh rupiah banda -1000
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
            rb     > join agent 404040 02 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Central Clinic.
            rb     > join clinic kdh rupiah banda -1000
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
            rb     > join clinic kdh rupiah banda -1000
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
            +260979565991     > join clinic 202020 support 1 1000
            +260979565991     < Hi Support 1, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565992     > join clinic 202020 support 2 1000
            +260979565992     < Hi Support 2, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565993     > join clinic 202020 support 3 1000
            +260979565993     < Hi Support 3, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        admins = Contact.objects.all()
        for admin in admins:
            admin.is_help_admin = True
            admin.save()
        time.sleep(1)
        # create clinic workers
        script = """
            +260979565994     > join clinic 202020 James Phiri 1000
            +260979565994     < Hi James Phiri, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565995     > join clinic 202020 James Banda 1000
            +260979565995     < Hi James Banda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            +260979565996     > join clinic 202020 Peter Kunda 1000
            +260979565996     < Hi Peter Kunda, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)

        # create CBA's
        script = """
            +260977777751     > join agent 202020 02 rupiah banda
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
        cba = Contact.objects.get(connection=None, name="Kunda Banda")
        self.assertEqual(cba.is_active, False)
        self.assertEqual(Connection.objects.filter(contact=cba).count(), 0)

        #test deregistering cba whose name is not unique in system but at clinic
        script = """
            +260979565996 > deregister rupiah BandA
            +260979565991 < Peter Kunda:+260979565996 has deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
            +260979565992 < Peter Kunda:+260979565996 has deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
            +260979565993 < Peter Kunda:+260979565996 has deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
            +260979565996 < You have successfully deregistered Rupiah Banda:+260977777751 of zone 02 at Kafue District Hospital
        """
        self.runScript(script)
        cba = Contact.objects.get(connection=None, name="Rupiah Banda")
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
        cba = Contact.objects.get(connection=None, name="Trevor Sinkala")
        self.assertEqual(cba.is_active, False)

        self.assertTrue(Message.objects.filter(contact=cba) > 0)
        self.assertTrue(Message.objects.filter(connection__contact=None).count() > 3)
        self.assertEqual(Message.objects.filter(connection=None).count(), 0)

        script = """
            +260977777756 > cba who deregistered me?
            +260977777756 < You must be registered with a clinic to use the broadcast feature. Please ask your clinic team how to register, or respond with keyword 'HELP'
            """
        self.runScript(script)
       

    def testChangeClinic(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        dst = LocationType.objects.create(slug=const.DISTRICT_SLUGS[0])
        prv = LocationType.objects.create(slug=const.PROVINCE_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)
        mansa = Location.objects.create(name="Mansa",
                                        slug="403000", type=dst)
        luapula = Location.objects.create(name="Luapula",
                                          slug="400000", type=prv)
        script = """
            tk     > join clinic kdh tizie kays 1000
            tk     < Hi Tizie Kays, thanks for registering for Results160 from Kafue District Hospital. Your PIN is 1000. Reply with keyword 'HELP' if this is incorrect
            hubman     > join hub 403012 hubman banda 1234
            hubman     < Hi Hubman Banda, thanks for registering for Results160 from hub at Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            dho     > join dho 4030 Dho banda 1234
            dho     < Hi Dho Banda, thanks for registering for Results160 from Mansa DHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            pho     > join pho 40 Pho banda 1234
            pho     < Hi Pho Banda, thanks for registering for Results160 from Luapula PHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)

        old_contact = Contact.active.get(connection__identity='tk')
        old_contact_id = old_contact.id

        script = """
            tk     > change clinic
            tk     < To change your registration status from one clinic to another send <CHANGE CLINIC> <NEW CLINIC CODE> E.g. Change clinic 111111
            tk     > change location 22 44
            tk     < To change your registration status from one clinic to another send <CHANGE CLINIC> <NEW CLINIC CODE> E.g. Change clinic 111111
            tk     > change clinic kdh
            tk     < You already belong to Kafue District Hospital which has clinic code kdh
            tk     > change clinic 403012
            tk     < Thank you Tizie Kays! You have successfully changed your location from Kafue District Hospital to Central Clinic.
            tk     > change clinic 403000
            tk     < Sorry, I don't know about a location with code 403000. Please check your code and try again.
            hubman     > change clinic 403012
            hubman     < You are not registered as a clinic worker. Please respond with HELP to be assisted.
            dho     > change clinic dho 4030 Dho banda 1234
            dho     < You are not registered as a clinic worker. Please respond with HELP to be assisted.
            pho     > change clinic whatever
            pho     < You are not registered as a clinic worker. Please respond with HELP to be assisted.
            """
        self.runScript(script)

        old_contact = Contact.objects.get(id=old_contact_id)
        self.assertTrue(old_contact.default_connection == None)
        self.assertEqual(old_contact.is_active, False)
        self.assertEqual(old_contact.location, kdh)

        new_contact  = Contact.active.get(connection__identity='tk')
        # @type new_contact Contact
        self.assertEqual(new_contact.location, central_clinic)
        self.assertEqual(new_contact.name, 'Tizie Kays')
        