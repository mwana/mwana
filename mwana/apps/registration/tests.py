"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.locations.models import Location, LocationType

from mwana import const


class TestApp(TestScript):
    apps = (handler_app,)
    
    def testRegistration(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create()
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        central_clinic = Location.objects.create(name="Central Clinic",
                                      slug="403012", type=ctr)
        script = """
            lost   > join
            lost   < To register, send JOIN <CLINIC CODE> <NAME> <SECURITY CODE>
            rb     > join kdh rupiah banda 1234
            rb     < Hi Rupiah Banda, thanks for registering for DBS results from Results160 as staff of Kafue District Hospital. Reply with keyword 'HELP' if your information is not correct.
            kk     > join whoops kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code whoops. Please check your code and try again.
            noname > join abc
            noname < Sorry, I didn't understand that. Make sure you send your location, name and pin like: JOIN <CLINIC CODE> <NAME> <SECURITY CODE>.
        """
        self.runScript(script)
        self.assertEqual(1, Contact.objects.count(), "Registration didn't create a new contact!")
        rb = Contact.objects.all()[0]
        self.assertEqual("Rupiah Banda", rb.name, "Name was not set correctly after registration!")
        self.assertEqual(kdh, rb.location, "Location was not set correctly after registration!")
        self.assertEqual(rb.types.count(), 1)
        self.assertEqual(rb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)


        script = """
            jb     > join 4o30i2 jacob banda 1234
            jb     < Hi Jacob Banda, thanks for registering for DBS results from Results160 as staff of Central Clinic. Reply with keyword 'HELP' if your information is not correct.
            kk     > join 4f30i2 kenneth kaunda 1234
            kk     < Sorry, I don't know about a location with code 4f30i2. Please check your code and try again.
        """
        self.runScript(script)
        self.assertEqual(2, Contact.objects.count())
        jb = Contact.objects.get(name='Jacob Banda')
        self.assertEqual(central_clinic, jb.location)
        self.assertEqual(jb.types.count(), 1)
        self.assertEqual(jb.types.all()[0].slug, const.CLINIC_WORKER_SLUG)