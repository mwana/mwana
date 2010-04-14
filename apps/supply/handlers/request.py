#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers import KeywordHandler
from mwana.apps.supply.models import SupplyType


class RequestHandler(KeywordHandler):
    """
    """

    keyword = "request|req"

    def help(self):
        self.respond("To request more supplies, send REQ <SUPPLY CODE>")

    def handle(self, text):
        supply_codes = text.split(" ")
        found_supplies = []
        unknown_supplies = []
        for code in supply_codes:
            try:
                supply = SupplyType.objects.get(slug__iexact=code)
                found_supplies.append(supply)
            except SupplyType.DoesNotExist:
                unknown_supplies.append(code)
        if found_supplies:
            self.respond("Your request for more %(supplies)s has been received.",
                         supplies=" and ".join([supply.name for supply in found_supplies]))
        if unknown_supplies:
            self.respond("Sorry, I don't know about any supplies with code %(supplies)s.",
                            supplies=" or ".join([code for code in unknown_supplies]))
