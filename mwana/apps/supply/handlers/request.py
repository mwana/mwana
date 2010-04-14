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
        self.respond("To request more supplies, send REQUEST <SUPPLY CODE>")

    def handle(self, text):
        supply_codes = text.split(" ")
        
        if not self.msg.contact:
            self.respond("Sorry you have to register to request supplies. %s" %\
                         RegisterHandler.HELP_TEXT)
            return
        
        # for convenience
        contact  = self.msg.contact
        location = self.msg.contact.location
        
        created_supplies = []
        pending_supplies = []
        unknown_supplies = []
        for code in supply_codes:
            try:
                supply = SupplyType.objects.get(slug__iexact=code)
                
                # check for pending requests
                try: 
                    # if the below doesn't fail we already have a pending request
                    pending = SupplyRequest.active_for_location(location).get(type=supply)
                    pending_supplies.append(pending)
                
                except SupplyRequest.DoesNotExist:
                    # normal flow -- create a new supply request for this 
                    request = SupplyRequest.objects.create(type=supply, status="requested",
                                                           location=self.msg.contact.location,
                                                           requested_by=self.msg.contact)
                    created_supplies.append(supply)
            
            except SupplyType.DoesNotExist:
                unknown_supplies.append(code)
        
        if created_supplies:
            self.respond("Your request for more %(supplies)s has been received.",
                         supplies=" and ".join([supply.name for supply in created_supplies]))
        
        if unknown_supplies:
            self.respond("Sorry, I don't know about any supplies with code %(supplies)s.",
                            supplies=" or ".join([code for code in unknown_supplies]))
        
        if pending_supplies:
            self.respond("You already have requested %(supplies)s. To check status send STATUS <SUPPLY CODE>.",
                         supplies=" and ".join([supply.type.name for supply in pending_supplies]))
        
        