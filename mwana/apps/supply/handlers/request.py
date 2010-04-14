#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from mwana.apps.supply.models import SupplyType, SupplyRequest
from .register import RegisterHandler

class RequestHandler(KeywordHandler):
    """
    """

    keyword = "request|req"

    def help(self):
        self.respond("To request more supplies, send REQ <SUPPLY CODE>")

    def handle(self, text):
        supply_codes = text.split(" ")
        
        if not self.msg.contact:
            self.respond("Sorry you have to register to request supplies. %s" %\
                         RegisterHandler.HELP_TEXT)
            return
        
        found_supplies = []
        unknown_supplies = []
        for code in supply_codes:
            try:
                supply = SupplyType.objects.get(slug__iexact=code)
                # create a new supply request for this 
                # TODO: parse out the location
                # TODO: check for pending requests
                request = SupplyRequest.objects.create(type=supply, status="requested",
                                                       location=self.msg.contact.location,
                                                       requested_by=self.msg.contact)
                found_supplies.append(supply)
            except SupplyType.DoesNotExist:
                unknown_supplies.append(code)
        if found_supplies:
            self.respond("Your request for more %(supplies)s has been received.",
                         supplies=" and ".join([supply.name for supply in found_supplies]))
        if unknown_supplies:
            self.respond("Sorry, I don't know about any supplies with code %(supplies)s.",
                            supplies=" or ".join([code for code in unknown_supplies]))
