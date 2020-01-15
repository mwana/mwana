# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.phia.models import PhiaModel
import time

from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript


class TestApp(TestScript):
#    apps = (cleaner_App, handler_app, )
   
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
            jb     > join clinic 4o30i2 jacob banda 1234
            jb     < Hi Jacob Banda, thanks for registering for Results160 from Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kk     > join clinic 4f30i2 kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code 4f3012. Please check your code and try again.
        """
        self.runScript(script)
        time.sleep(1)
        self.assertEqual(1, Contact.objects.count())
        jb = Contact.objects.get(name='Jacob Banda')
        self.assertEqual(central_clinic, jb.location)
        self.assertEqual(jb.types.count(), 1)
        self.assertEqual(jb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)

        script = """
            hubman     > join hub 4o30i2 hubman banda 1234
            hubman     < Hi Hubman Banda, thanks for registering for Results160 from hub at Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect           
            dho     > join dho 4030 Dho banda 1234
            dho     < Hi Dho Banda, thanks for registering for Results160 from Mansa DHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect           
            pho     > join pho 40 Pho banda 1234
            pho     < Hi Pho Banda, thanks for registering for Results160 from Luapula PHO. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect           
            labman     > join lab 4o30i2 mark zuckerberg 1234
            labman     < Hi Mark Zuckerberg, thanks for registering for Results160 from lab at Central Clinic. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            kdh_man     > join phia kdh James Bond 1234
            kdh_man     < Hi James Bond, thanks for registering as a ZAMPHIA2020 RoR & LTC SMS user at Kafue District Hospital. Your PIN is 1234. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        

        script = """
            phia_man     > join phia 403012 broken hill 2345
            phia_man     < Hi Broken Hill, thanks for registering as a ZAMPHIA2020 RoR & LTC SMS user at Central Clinic. Your PIN is 2345. Reply with keyword 'HELP' if this is incorrect
            phia_lady     > join phia 403012 lady gaga 2345
            phia_lady     < Hi Lady Gaga, thanks for registering as a ZAMPHIA2020 RoR & LTC SMS user at Central Clinic. Your PIN is 2345. Reply with keyword 'HELP' if this is incorrect
            """
        self.runScript(script)
        time.sleep(.5)
        self.assertEqual(8, Contact.objects.count())
        phiaman = Contact.objects.get(name='Broken Hill')
        self.assertEqual(phiaman.types.all()[0].slug, const.PHIA_WORKER_SLUG)
        
        script = """
            phia_man     > LTC NEW
            phia_man     < Please specify one valid temporary ID
            phia_man     > LTC NEW 1234567
            phia_man     < Please reply with your PIN to save linkage for 1234567
            phia_man     > 1111
            phia_man     < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man     > 2345
            phia_man     < Clinical interaction for 1234567 confirmed
            """
        self.runScript(script)
       
        script = """
            phia_man     > ROR DEMO 403012
            phia_man     < Central Clinic has 3 results ready. Please reply to this SMS with your pin code to retrieve them.
            phia_lady     < Central Clinic has 3 results ready. Please reply to this SMS with your pin code to retrieve them.
            phia_man     > 234
            phia_man     < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man     > 2345
            phia_lady    < Broken Hill has collected these results
            phia_man     < Thank you! Here are your results: **** 9990;CD200;VL500. **** 9991;CD250;VL300. **** 9992;CD650;VL100
            phia_man     < Please record these results in your clinic records and promptly delete them from your phone.  Thank you again Broken Hill!
            phia_lady    > 2345
            phia_lady    < Hello Lady Gaga. Are you trying to retrieve new results? There are no new results ready for you. We shall let you know as soon as they are ready.
            """
        self.runScript(script)

         #todo: ask for pin even for demo results
        script = """
            phia_man     > ROR CHECK
            phia_man     < Central Clinic has no new results ready right now. You will be notified when new results are ready.
            phia_man     > ROR CHECK 403012
            phia_man     < Central Clinic has no new results ready right now. You will be notified when new results are ready.
            phia_man     > ROR CHECK 9990
            phia_man     < Please reply with your PIN to view the results for 9990
            phia_man     > 12
            phia_man     < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man     > 2345
            phia_man     < Here are your results: **** 9990;CD200;VL500.
            phia_man     > ROR CHECK 9991
            phia_man     < Please reply with your PIN to view the results for 9991
            phia_man     > 2345
            phia_man     < Here are your results: **** 9991;CD200;VL500.
            """
        self.runScript(script)

        script = """
            phia_man     > LTC DEMO 403012
            phia_man     < Central Clinic has 2 ALTC & 1 passive participant to link to care. Please reply with your PIN code to get details of ALTC participants.
            phia_lady    < Central Clinic has 2 ALTC & 1 passive participant to link to care. Please reply with your PIN code to get details of ALTC participants.
            phia_man     > 234
            phia_man     < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man     > 2345
            phia_lady    < Broken Hill has collected these results
            phia_man     < LTC: Banana Nkonde;14 Munali, Lusaka;9990 ****. Sante Banda;12 Minestone, Lusaka;9991 ****
            phia_man     < Please record these details in your LTC Register immediately and promptly delete them from your phone. Thank you again!
            phia_lady    > 2345
            phia_lady    < Hello Lady Gaga. Are you trying to retrieve new results? There are no new results ready for you. We shall let you know as soon as they are ready.
            """
        self.runScript(script)

        #todo: ask for pin even for demo results
        script = """
            phia_man     > LTC CHECK
            phia_man     <  Central Clinic has 2 ALTC & 1 passive participant to link to care. Please reply with your PIN code to get details of ALTC participants
            phia_man     > 11
            phia_man     < Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'
            phia_man     > 2345
            phia_man     < LTC: Banana Nkonde;14 Munali, Lusaka;9990 ****. Sante Banda;12 Minestone, Lusaka;9991 ****
            phia_man     > LTC CHECK 9990
            phia_man     < LTC: Banana Nkonde;14 Munali, Lusaka;9990
            phia_man     > LTC CHECK 9991
            phia_man     < LTC: Banana Nkonde;14 Munali, Lusaka;9991
            """
        self.runScript(script)

        

   