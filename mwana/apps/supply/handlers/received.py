# vim: ai ts=4 sts=4 et sw=4
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.supply.models import SupplyType, SupplyRequest
from mwana.apps.registration.handlers.register import RegisterHandler

class ReceivedHandler(KeywordHandler):
    """
    """

    keyword = "received|rec|got"

    def help(self):
        self.respond("To report receiving supplies, send GOT <SUPPLY CODE>")

    def handle(self, text):
        
        if not self.msg.contact:
            self.respond("Sorry you have to register to report supplies. %s" %\
                         RegisterHandler.HELP_TEXT)
            return
        
        # for convenience
        contact  = self.msg.contact
        location = self.msg.contact.location
        
        processed_supplies = []
        inactive_supplies = []
        unknown_supplies = []
        supply_codes = text.split(" ")
        for code in supply_codes:
            try:
                supply = SupplyType.objects.get(slug__iexact=code)
                
                # check for pending requests
                try: 
                    # if the below doesn't fail we already have a pending request
                    pending = SupplyRequest.active().get(location=location, type=supply)
                    pending.status = "delivered"
                    pending.save()
                    processed_supplies.append(pending)
                
                except SupplyRequest.DoesNotExist:
                    # this was a known supply type, but we didn't have an active request
                    inactive_supplies.append(supply)
            
            except SupplyType.DoesNotExist:
                unknown_supplies.append(code)
        
        if processed_supplies:
            self.respond("Your confirmation that %(supplies)s were delivered has been received. Enjoy your new stuff!",
                         supplies=" and ".join([supply.type.name for supply in processed_supplies]))
        
        if inactive_supplies:
            self.respond("You don't have any active requests for %(supplies)s.",
                         supplies=" and ".join([supply.name for supply in inactive_supplies]))
        
        if unknown_supplies:
            self.respond("Sorry, I don't know about any supplies with code %(supplies)s.",
                            supplies=" or ".join([code for code in unknown_supplies]))
        
        