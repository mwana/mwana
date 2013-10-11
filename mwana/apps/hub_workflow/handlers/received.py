# vim: ai ts=4 sts=4 et sw=4
import re
import logging
from django.conf import settings
from mwana.apps.hub_workflow.models import HubSampleNotification
from mwana.apps.locations.models import Location
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

UNGREGISTERED = "Sorry, you must be registered with Results160 to report DBS samples sent. If you think this message is a mistake, respond with keyword 'HELP'"
SENT          = "Hello %(name)s! We received your notification that you received %(count)s  DBS samples today from %(clinic)s."
HELP          = "To report DBS samples received, send RECEIVED <NUMBER OF SAMPLES> <CLINIC-CODE>"
SORRY         = "Sorry, we didn't understand that message."
logger = logging.getLogger(__name__)


class ReceivedHandler(KeywordHandler):
    """
    """

    keyword = "received|recieved|receive|recieve"
    PATTERN = re.compile(r"^(.+)(\s+)(\d+)$")

    def help(self):
        self.respond(HELP)

    def get_only_number(self, text):
        reg = re.compile(r'\d+')
        nums = reg.findall(text)
        if len(nums) == 1:
            return nums[0]
        else:
            return None

    def handle(self, text):
        if not self.msg.contact:
            self.respond(UNGREGISTERED)
            return

        group = self.PATTERN.search(text)
        if group is None:
            self.respond("%s %s " % (SORRY, HELP))
            return False

        tokens = group.groups()
        if not tokens:
            self.respond("%s %s " % (SORRY, HELP))
            return False
        original_text_count = text = raw_count = tokens[0]
        clinic = None
        slug = tokens[2].strip()[:6]
        try:
            clinic = Location.objects.get(slug__iexact=slug)
        except Location.DoesNotExist:
            self.respond("Sorry, I don't about a location with code '%s'" % slug)
            return False

        b = InputCleaner()
        try:
            raw_count = b.remove_dash_plus(raw_count)
            count = int(b.try_replace_oil_with_011(raw_count))
        except (ValueError, TypeError):
            count = b.words_to_digits(raw_count)
            if not raw_count:
                raw_count = self.get_only_number(original_text_count)
                if raw_count:
                    count = int(raw_count)
                else:
                    self.respond("%s %s" % (SORRY, HELP))
                    return
            else:
                logger.info("Converted %s to %s" % (original_text_count, text))
                count = int(count)
                count = abs(count) #just in case we change our general cleaning routine

        if count < 1:
            self.respond("Sorry, the number of DBS samples received must be greater than 0 (zero).")
            return

        max_len = settings.MAX_SMS_LENGTH

        HubSampleNotification.objects.create(contact=self.msg.contact,
                                             lab=self.msg.contact.location,
                                             count=count, count_in_text=
                                             original_text_count[0:max_len],
                                             clinic=clinic)
        self.respond(SENT, name=self.msg.contact.name, count=count,
                     clinic=clinic.name)


