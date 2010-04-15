"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.locations.models import Location, LocationType


class TestApp(TestScript):
    apps = (handler_app,)
    
    def testRegistration(self):
        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create()
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        script = """
            lost   > join
            lost   < To register, send JOIN <LOCATION CODE> <NAME>
            rb     > join kdh rupiah banda
            rb     < Thank you for registering, rupiah banda! I've got you at Kafue District Hospital.
            kk     > join whoops kenneth kaunda
            kk     < Sorry, I don't know about a location with code whoops. Please check your code and try again.
            noname > join abc
            noname < Sorry, I didn't understand that. Make sure you send your location and name like: JOIN <LOCATION CODE> <NAME>
        """
        self.runScript(script)
        self.assertEqual(1, Contact.objects.count(), "Registration didn't create a new contact!")
        rb = Contact.objects.all()[0]
        self.assertEqual("rupiah banda", rb.name, "Name was not set correctly after registration!")
        self.assertEqual(kdh, rb.location, "Location was not set correctly after registration!")
