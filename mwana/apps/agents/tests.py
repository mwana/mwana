# vim: ai ts=4 sts=4 et sw=4
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.locations.models import Location, LocationType

from mwana.apps.reminders import models as reminders
from mwana import const


class TestApp(TestScript):
    
    def testAgentRegistration(self):
        self.assertEqual(0, Contact.objects.count())
        clinic = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=clinic)
        kdh = Location.objects.create(name="Mansa Central Clinic",
                                      slug="mansa", type=clinic)
        reminders.Event.objects.create(name="Birth", slug="birth|bith")
        self.assertEqual(reminders.Event.objects.count(), 1)
        script = """
            lost   > agent
            lost   < To register as a RemindMi agent, send AGENT <CLINIC CODE> <ZONE #> <YOUR NAME>
            rb     > agent kdh 02 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 02 of Kafue District Hospital. Please notify us next time there is a birth in your zone.
            rb     > agent kdh 03 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 03 of Kafue District Hospital. Please notify us next time there is a birth in your zone.
            rb     > agent kdh 03 rupiah banda
            rb     < Hello Rupiah Banda! You are already registered as a RemindMi Agent for zone 03 of Kafue District Hospital. 
            rb     > agent mansa 01 rupiah banda
            rb     < Hello Rupiah Banda! You are already registered as a RemindMi Agent for Kafue District Hospital. To leave your current clinic and join Mansa Central Clinic, reply with LEAVE and then re-send your message.
            rb     > leave
            rb     < You have successfully unregistered, Rupiah Banda. We're sorry to see you go.
            rb     > agent mansa 01 rupiah banda
            rb     < Thank you Rupiah Banda! You have successfully registered as a RemindMi Agent for zone 01 of Mansa Central Clinic. Please notify us next time there is a birth in your zone.
            kk     > agent whoops 03 kenneth kaunda
            kk     < Sorry, I don't know about a clinic with code whoops. Please check your code and try again.
            noname > agent abc
            noname < Sorry, I didn't understand that. To register as a RemindMi agent, send AGENT <CLINIC CODE> <ZONE #> <YOUR NAME>
        """
        self.runScript(script)
        self.assertEqual(2, Contact.objects.count()) # 1 for mansa, one for kdh
        rb = Contact.objects.all()[0]
        self.assertEqual("Rupiah Banda", rb.name, "Name was not set correctly after registration!")
        self.assertEqual(rb.location.slug, "03", "Location was not set correctly after registration!")
        self.assertEqual(rb.types.count(), 1)
        self.assertEqual(rb.types.all()[0].slug, 'cba')
