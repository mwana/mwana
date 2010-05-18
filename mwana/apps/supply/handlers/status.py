
from mwana.apps.supply.models import STATUS_CHOICES
from mwana.apps.supply.models import SupplyRequest
from mwana.apps.supply.models import SupplyType
from rapidsms.contrib.handlers import KeywordHandler
from mwana.apps.registration.handlers.register import RegisterHandler
import re

class StatusHandler(KeywordHandler):
    """
    A class that gives the requester the status about their request
    """
    keyword = "status|stat|state"

    def help(self):
        self.respond("To find out the status of an item send STATUS <SUPPLY CODE>")

    def get_choice_text(self, choice_id):
        """
        serves same purpose as django's get_status_display()
        """
        toReturn = None
        for id, text in STATUS_CHOICES:
            if id == choice_id:
                toReturn = text
                break
        return toReturn

    def handle(self, text):
        #If contact is not registered inform them and do not proceed to check requests
        if self.msg.contact == None:
                self.respond("Seems you are not registered. %s" % RegisterHandler.HELP_TEXT)
                return

        supply_items = set(re.findall('\S+', text))
        request = None
        supply_requests=None
        try:
            for supply_item in supply_items:
                try:
                    supply_type = SupplyType.objects.get(slug=supply_item)
                except:
                    self.respond("Supply %s not found." % (supply_item))
                    continue

                supply_requests = SupplyRequest.active().filter(type=supply_type)
                if supply_requests:
                    match = False
                    for request in supply_requests:
                        if request.requested_by:
                            if request.requested_by == self.msg.contact:
                                self.respond("Your request for %(supply)s has status: %(status)s as of %(date)s.",
                                             supply=request.type.name, status=request.get_status_display().upper(),
                                             date=request.modified.strftime("%B %d, %Y at %I:%M:%S %p"))
                                match = True
                    if not match:
                        self.respond("Request for %s by %s not found" % (supply_type, self.msg.contact))
                else:
                    self.respond("Request for %s by %s not found" % (supply_type, self.msg.contact))
        except Exception, e:
            self.error(e)
