#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.handlers.app import App as handler_app
from mwana.apps.supply.app import App
from mwana.apps.supply.models import SupplyType, SupplyRequest

class TestApp (TestScript):
    apps = (handler_app, App,)
    fixtures = ['camping_supplies']
    
    def testBootstrap(self):
        self.assertEqual(4, SupplyType.objects.count())
        
    testSMSFlow = """
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
        