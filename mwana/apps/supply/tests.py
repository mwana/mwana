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

        # make sure you can't request two of the same item
        script = """
            sguy > request sb
            sguy < You already have requested sleeping bags. To check status send STATUS <SUPPLY CODE>.
        """
        self.runScript(script)
        self.assertEqual(1, SupplyRequest.objects.count())

        # unless it has been delivered
        request.status = "delivered"
        request.save()
        script = """
            sguy > request sb
            sguy < Your request for more sleeping bags has been received.
        """
        self.runScript(script)
        self.assertEqual(2, SupplyRequest.objects.count())

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

    def testStatus(self):
        # test unknown user
        script = """
            sguy > status sb
            sguy < Seems you are not registered
        """
        self.runScript(script)

        self.assertEqual(0, SupplyRequest.objects.count())
        # register a contact first
        location = Location.objects.get(slug="uth")
        contact = self._create_contact("sguy", "supply guy", location)

        # unmatched status request
        script = """
            sguy > request sb
            sguy < Your request for more sleeping bags has been received.
            sguy > status tent    
            sguy < Request for tents by supply guy not found
            sguy > status mm
            sguy < Request for marshmallows by supply guy not found
            sguy > status hl
            sguy < Request for head lamps by supply guy not found
            sguy > status strange_supply
            sguy < Supply strange_supply not found.
        """
        self.runScript(script)

        # matched status request
        request = SupplyRequest.objects.all()[0]
        date = request.modified.strftime("%B %d, %Y at %I:%M:%S %p")
        
        text = """
            sguy > status sb
            sguy < Your request for sleeping bags has status: YET TO BE PROCESSED as of %(date)s.
        """ % {"date": date}
        
        script=text.strip()
        self.runScript(script)


       

    testRequestRequiresRegistration = """
        noname > request sb
        noname < Sorry you have to register to request supplies. To register, send JOIN <LOCATION CODE> <NAME>
    """

    def _create_contact(self, identity, name, location):
        # this has a janky dependency on the reg format, but is nice and convenient
        reg_script = """
            %(identity)s > join %(loc_code)s %(name)s
            %(identity)s < Thank you for registering, %(name)s! I've got you at %(loc_name)s.
        """ % {"identity": identity, "name": name, 
               "loc_code": location.slug, "loc_name": location.name}
        self.runScript(reg_script)
        return Contact.objects.get(connection__identity=identity, location=location, name=name)
        