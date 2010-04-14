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
        
    
    testRequestRequiresRegistration = """
        noname > request sb
        noname < Sorry you have to register to request supplies. To register, send JOIN <LOCATION CODE> <NAME>
    """
    
    def testRequest(self):
        self.assertEqual(0, SupplyRequest.objects.count())
        # have to be a registered contact first
        location = Location.objects.get(slug="uth")
        contact = self._create_contact("sguy", "supply guy", location)
        
        script = """
            sguy > request sb
            sguy < Your request for more sleeping bags has been received.
        """
        self.runScript(script)
        self.assertEqual(1, SupplyRequest.objects.count())
        request = SupplyRequest.objects.all()[0]
        self.assertEqual("sb", request.type.slug)
        self.assertEqual(contact, request.requested_by)
        self.assertEqual(location, request.location)
        self.assertEqual("requested", request.status)
        
        # some error conditions
        script = """
            sguy > request noods
            sguy < Sorry, I don't know about any supplies with code noods.
            sguy > request noods lighter
            sguy < Sorry, I don't know about any supplies with code noods or lighter.
            sguy > request tent noods
            sguy < Your request for more tents has been received.
            sguy < Sorry, I don't know about any supplies with code noods.
        """
        self.runScript(script)

    def _create_contact(self, identity, name, location):
        # this has a janky dependency on the reg format, but is nice and convenient
        reg_script = """
            %(identity)s > join %(loc_code)s %(name)s
            %(identity)s < Thank you for registering, %(name)s! I've got you at %(loc_name)s.
        """ % {"identity": identity, "name": name, 
               "loc_code": location.slug, "loc_name": location.name}
        self.runScript(reg_script)
        return Contact.objects.get(connection__identity=identity, location=location, name=name)
        