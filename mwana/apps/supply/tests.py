#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.supply.app import App
from mwana.apps.supply.models import SupplyType, SupplyRequest
from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript

class TestApp (TestScript):
    apps = (handler_app, App,)
    fixtures = ['camping_supplies', 'health_centers']
    
    def testBootstrap(self):
        self.assertEqual(4, SupplyType.objects.count())
        
        
    def testRegistration(self):
        self.assertEqual(0, Contact.objects.count())
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
        kdh = Location.objects.get(slug="kdh")
        self.assertEqual("rupiah banda", rb.name, "Name was not set correctly after registration!")
        self.assertEqual(kdh, rb.location, "Location was not set correctly after registration!")
        
    
    testRequestSMSFlow = """
            nancy > request tent
            nancy < Your request for more tents has been received.
            nancy > request tent mm
            nancy < Your request for more tents and marshmallows has been received.
            nancy > request noods
            nancy < Sorry, I don't know about any supplies with code noods.
            nancy > request noods lighter
            nancy < Sorry, I don't know about any supplies with code noods or lighter.
            nancy > request tent noods
            nancy < Your request for more tents has been received.
            nancy < Sorry, I don't know about any supplies with code noods.
        """
        
    def testRequest(self):
        self.assertEqual(0, SupplyRequest.objects.count())
        testSMSFlow = """
            trevor > request sb
            trevor < Your request for more sleeping bags has been received.
        """
        self.runScript(testSMSFlow)
        self.assertEqual(1, SupplyRequest.objects.count())
        request = SupplyRequest.objects.all()[0]
        self.assertEqual("sb", request.type.slug)
        