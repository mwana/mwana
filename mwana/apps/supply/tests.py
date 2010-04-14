#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.tests.scripted import TestScript
from mwana.apps.supply.app import App


class TestApp (TestScript):
    apps = (App,)
    fixtures = ['camping_supplies']
    
    testBasic = """
        nancy > request tent
        nancy < Your request for more tents has been received.
        tobias > request sb
        tobias < Your request for more sleeping bags has been received.
    """
    