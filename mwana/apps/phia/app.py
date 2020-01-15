# vim: ai ts=4 sts=4 et sw=4


from mwana.apps.phia.mocking import MockLtcUtility
import logging
import rapidsms
import re
from mwana.apps.labresults.messages import *
from mwana.apps.phia.mocking import MockResultUtility
from mwana.util import get_clinic_or_default
import mwana.const as const

logger = logging.getLogger(__name__)


class App(rapidsms.apps.base.AppBase):
    # we store everyone who we think could be sending us a PIN for results
    # here, so we can intercept the message.
    waiting_for_pin = {}

    # we keep a mapping of locations to who collected last, so we can respond
    # when we receive stale pins
    last_collectors = {}
    

    mocker = MockResultUtility()
    ltc_mocker = MockLtcUtility()

    # regex format stolen from KeywordHandler
    CHECK_KEYWORD = "ROR CHECK|ROR CHEK|ROR CHK"
    CHECK_REGEX = r"^(?:%s)(?:[\s,;:]+(.+))?$" % (CHECK_KEYWORD)

    LTC_CHECK_KEYWORD = "LTC CHECK|LTC CHEK|LTC CHK"
    LTC_CHECK_REGEX = r"^(?:%s)(?:[\s,;:]+(.+))?$" % (LTC_CHECK_KEYWORD)

    LTC_NEW_REGEX = r"^(?:%s)(?:[\s,;:]+(.+))?$" % ("LTC NEW")

    def start(self):
        pass


    def handle(self, message):
        if not message.contact:
            return False
        if not (message.contact.is_active  and const.get_phia_worker_type() in message.connection.contact.types.all()):
            return False
        key = message.text.strip().upper()
        key = key[:4]

        if re.match(self.CHECK_REGEX, message.text, re.IGNORECASE):
            clinic = get_clinic_or_default(message.contact)
            tokens = message.text.split()
            if len(tokens) == 3 and tokens[2] in ["9990", "9991", "9992"]:
                self.waiting_for_pin[message.connection] = "Here are your results: **** %s;CD200;VL500." % tokens[2]
                message.respond("Please reply with your PIN to view the results for %(req_id)s", req_id=tokens[2])
#                message.respond("Here are your results: **** %(req_id)s;CD200;VL500.", req_id=tokens[2])
            else:
                message.respond("%(clinic)s has no new results ready right now. You will be notified when new results are ready.", clinic=clinic.name)
            return True
        if re.match(self.LTC_NEW_REGEX, message.text, re.IGNORECASE):
            clinic = get_clinic_or_default(message.contact)
            tokens = message.text.split()
            if len(tokens) == 3:
                self.waiting_for_pin[message.connection] = "Clinical interaction for %s confirmed" % tokens[2]
                message.respond("Please reply with your PIN to save linkage for %(req_id)s", req_id=tokens[2])
            else:
                message.respond("Please specify one valid temporary ID")
            return True
        if re.match(self.LTC_CHECK_REGEX, message.text, re.IGNORECASE):
            clinic = get_clinic_or_default(message.contact)
            tokens = message.text.split()
            if len(tokens) == 3 and tokens[2] in ["9990", "9991", "9992"]:
                #todo: ask for pin before sending
                message.respond("LTC: Banana Nkonde;14 Munali, Lusaka;%(req_id)s", req_id=tokens[2])
            elif len(tokens) == 3:
                message.respond("There are no LTC details for participant # %(req_id)s for %(clinic)s. Make sure you entered the correct #", clinic=clinic.name, req_id=tokens[2])
            else:                
                self.waiting_for_pin[message.connection] = "LTC: Banana Nkonde;14 Munali, Lusaka;9990 ****. Sante Banda;12 Minestone, Lusaka;9991 ****"
                message.respond("%(clinic)s has 2 ALTC & 1 passive participant to link to care. Please reply with your PIN code to get details of ALTC participants", clinic=clinic.name)
            return True
        elif self.mocker.handle(message):
            return True
        elif self.ltc_mocker.handle(message):
            return True
        elif message.connection in self.waiting_for_pin \
                and message.connection.contact:
            pin = message.text.strip()
            if pin.upper() == message.connection.contact.pin.upper():
                message.respond(self.waiting_for_pin[message.connection])
                self.waiting_for_pin.pop(message.connection)
                return True
            else:
                # lets hide a magic field in the message so we can respond
                # in the default phase if no one else catches this.  We
                # don't respond here or return true in case this was a
                # valid keyword for another app.
                message.possible_bad_pin = True
                logger.warning("bad pin %s" % message.text)

    def default(self, message):
        # collect our bad pin responses, if they were generated.  See comment
        # in handle()
        if hasattr(message, "possible_bad_pin"):
            message.respond(BAD_PIN)
            return True

        clinic = get_clinic_or_default(message.contact)
        if message.contact and message.contact.is_active  and const.get_phia_worker_type() in message.connection.contact.types.all() \
            and clinic in self.last_collectors \
            and message.text.strip().upper() == message.contact.pin.upper():
            if message.contact == self.last_collectors[clinic]:
                message.respond(SELF_COLLECTED, name=message.connection.contact.name)
            else:
                message.respond(ALREADY_COLLECTED, name=message.connection.contact.name,
                                collector=self.last_collectors[clinic])
            return True
        return self.mocker.default(message)

