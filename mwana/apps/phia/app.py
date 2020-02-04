# vim: ai ts=4 sts=4 et sw=4


from mwana.apps.phia.models import Result
from mwana.apps.labresults.messages import RESULTS_PROCESSED
from mwana.apps.labresults.messages import NOT_REGISTERED
from mwana.apps.labresults.messages import combine_to_length
from rapidsms.messages import OutgoingMessage
from mwana.apps.phia.mocking import MockLtcUtility
import logging
from mwana.apps.labtests.models import PreferredBackend

import mwana.const as const
import rapidsms
from django.db.models import Q
import re
from mwana.apps.labresults.messages import INSTRUCTIONS
from mwana.apps.phia.mocking import MockResultUtility
from mwana.util import get_clinic_or_default
import mwana.const as const
from mwana.apps.labresults.messages import settings
from mwana.apps.phia.models import Result
from datetime import date
from datetime import datetime
from rapidsms.models import Connection, Backend
from rapidsms.models import Contact

logger = logging.getLogger(__name__)


RESULTS = "Here are your results: "


def is_eligible_for_phia_results(contact):
    return contact and contact.is_active  and const.get_phia_worker_type() in contact.types.all() \

class App(rapidsms.apps.base.AppBase):
    # we store everyone who we think could be sending us a PIN for results
    # here, so we can intercept the message.
    waiting_for_pin = {}
    waiting_for_linkage_pin = {}
    waiting_for_demo_results_pin = {}
    waiting_for_ltc_pin = {}

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
        """Configure your app in the start phase."""
#        self.schedule_notification_task()
#        self.schedule_process_payloads_tasks()
#        self.schedule_participant_notification_task()

    def pop_pending_connection(self, connection):
        self.waiting_for_pin.pop(connection)

    def handle(self, message):
        if not message.contact:
            return False
        if not (message.contact.is_active and const.get_phia_worker_type() in message.connection.contact.types.all()):
            return False
        key = message.text.strip().upper()
        key = key[:4]

        if re.match(self.CHECK_REGEX, message.text, re.IGNORECASE):
            if not is_eligible_for_phia_results(message.contact):
                message.respond(NOT_REGISTERED)
                return True
            clinic = get_clinic_or_default(message.contact)
            tokens = message.text.split()
            if len(tokens) == 3 and tokens[2].upper() in ["DEMO9990", "DEMO9991", "DEMO9992"]:
                self.waiting_for_demo_results_pin[message.connection] = "Here are your results: **** %s;CD200;VL500." % tokens[2]
                message.respond("Please reply with your PIN to view the results for %(req_id)s", req_id=tokens[2])
                return True
            elif len(tokens) == 3:
                req_id = tokens[2]
                results = self._pending_results(clinic, req_id)
                if results:
                    message.respond("Please reply with your PIN to view the results for %(req_id)s", req_id=tokens[2])
                    self._mark_results_pending(results, [message.connection])
                    return True
                else:
                    message.respond("Central Clinic has no new results ready right now for %(req_id)s. You will be notified when new results are ready.", req_id=tokens[2])
                    return True
            results = self._pending_results(clinic)
            if results:
                message.respond("%(clinic)s has %(count)s results ready. Please reply with your PIN code to retrieve them.",
                clinic=clinic.name, count=results.count())
                self._mark_results_pending(results, [message.connection])
            else:
                message.respond("%(clinic)s has no new results ready right now. You will be notified when new results are ready.", clinic=clinic.name)
            return True
        if re.match(self.LTC_NEW_REGEX, message.text, re.IGNORECASE):
            if not is_eligible_for_phia_results(message.contact):
                message.respond(NOT_REGISTERED)
                return True
            clinic = get_clinic_or_default(message.contact)
            tokens = message.text.split()
            if len(tokens) == 3:
                results = Result.objects.filter(clinic=message.contact.clinic, linked=False, requisition_id=tokens[2].strip())
                if not results:
                    message.respond("There is no record with ID %(id)s to link. Make sure you typed the ID correctly and try again.", id=tokens[2])
                    return True
                self.waiting_for_linkage_pin[message.connection] = results
                message.respond("Please reply with your PIN to save linkage for %(req_id)s", req_id=tokens[2])
            else:
                message.respond("Please specify one valid temporary ID")
            return True
        if re.match(self.LTC_CHECK_REGEX, message.text, re.IGNORECASE):
            if not is_eligible_for_phia_results(message.contact):
                message.respond(NOT_REGISTERED)
                return True
            clinic = get_clinic_or_default(message.contact)
            tokens = message.text.split()
            if len(tokens) == 3 and tokens[2].upper() in ["DEMO9990", "DEMO9991", "DEMO9992"]:
                #todo: ask for pin before sending
                message.respond("LTC: Banana Nkonde;14 Munali, Lusaka;%(req_id)s", req_id=tokens[2])
            elif len(tokens) == 3:
                #todo: review
                results = Result.objects.filter(clinic=message.contact.clinic, linked=False, requisition_id=tokens[2].strip())
                if not results:
                    message.respond("There are no LTC details for participant with ID %(req_id)s for %(clinic)s. Make sure you entered the correct ID", clinic=clinic.name, req_id=tokens[2])
                    return True
                self.waiting_for_ltc_pin[message.connection] = results
                message.respond("Please reply with your PIN to save linkage for %(req_id)s", req_id=tokens[2])
            else:
                results = self._pending_ltc(message.contact.clinic)
                if not results:
                    message.respond("There are no new LTC details for %(clinic)s.", clinic=clinic.name)
                    return True
                self.waiting_for_ltc_pin[message.connection] = results
                message.respond("%(clinic)s has %(count)s ALTC to link to care. Please reply with your PIN code to get details of ALTC participants", count=results.count(), clinic=clinic.name)
            return True
        elif self.mocker.handle(message):
            return True
        elif self.ltc_mocker.handle(message):
            return True
        elif message.connection in self.waiting_for_demo_results_pin \
                and message.connection.contact:
            pin = message.text.strip()
            if pin.upper() == message.connection.contact.pin.upper():
                message.respond(self.waiting_for_demo_results_pin[message.connection])
                self.waiting_for_demo_results_pin.pop(message.connection)
                return True
            else:
                # lets hide a magic field in the message so we can respond
                # in the default phase if no one else catches this.  We
                # don't respond here or return true in case this was a
                # valid keyword for another app.
                message.possible_bad_pin = True
                logger.warning("bad pin %s" % message.text)
        elif message.connection in self.waiting_for_pin \
                and message.connection.contact:
            pin = message.text.strip()
            if pin.upper() == message.connection.contact.pin.upper():
                self.send_results_after_pin(message)
                return True
            else:
                # lets hide a magic field in the message so we can respond
                # in the default phase if no one else catches this.  We
                # don't respond here or return true in case this was a
                # valid keyword for another app.
                message.possible_bad_pin = True
                logger.warning("bad pin %s" % message.text)
        elif message.connection in self.waiting_for_linkage_pin \
                and message.connection.contact:
            pin = message.text.strip()
            if pin.upper() == message.connection.contact.pin.upper():
                self.process_linkage_after_pin(message)
                return True
            else:
                # lets hide a magic field in the message so we can respond
                # in the default phase if no one else catches this.  We
                # don't respond here or return true in case this was a
                # valid keyword for another app.
                message.possible_bad_pin = True
                logger.warning("bad pin %s" % message.text)
        elif message.connection in self.waiting_for_ltc_pin \
                and message.connection.contact:
            pin = message.text.strip()
            if pin.upper() == message.connection.contact.pin.upper():
                self.process_ltc_after_pin(message)
                return True
            else:
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
                message.respond("Hi %(name)s. It looks like you already collected your results. To check for new results reply with keyword 'ROR CHECK'", name=message.connection.contact.name)
            else:
                message.respond(ALREADY_COLLECTED, name=message.connection.contact.name,
                                collector=self.last_collectors[clinic])
            return True
        return self.mocker.default(message)

    def _result_verified(self):
        """
        Only return verified results or results which can't be verified
        due to constraints at the lab.
        """
        return Q(verified__isnull=True) | Q(verified=True)


    def _pending_results(self, clinic, req_id=None):
        """
        Returns the pending results for a clinic. This is limited to 9 results
        (about 3 SMSes) at a time, so clinics aren't overwhelmed with new
        results.
        """
        if settings.SEND_LIVE_LABRESULTS:

            results = Result.objects.filter(clinic=clinic,
                                            clinic__send_live_results=True,
                                            notification_status__in=['new', 'notified'])
            if req_id:
                return results.filter(self._result_verified()).filter(requisition_id=req_id)[:9]
            return results.filter(self._result_verified())[:9]
        else:
            return Result.objects.none()

    def _pending_ltc(self, clinic, req_id=None):
        """
        Returns the pending results for a clinic. This is limited to 9 results
        (about 3 SMSes) at a time, so clinics aren't overwhelmed with new
        results.
        """
        if settings.SEND_LIVE_LABRESULTS:

            results = Result.objects.filter(clinic=clinic,
                                            clinic__send_live_results=True,
                                            linked=False, # when should we stop if linkage not happening
                                            #todo: review
                                            notification_status__in=['sent'])
            if req_id:
                return results.filter(self._result_verified()).filter(requisition_id=req_id)[:9]
            return results.filter(self._result_verified())[:9]
        else:
            return Result.objects.none()

    def _mark_results_pending(self, results, connections):
        for connection in connections:
            self.waiting_for_pin[connection] = results
        for r in results:
            r.notification_status = 'notified'
            r.save()

    def send_results_after_pin(self, message):
        """
        Sends the actual results in response to the message
        (comes after PIN workflow).
        """
        results = self.waiting_for_pin[message.connection]
        clinic = get_clinic_or_default(message.contact)
        if not results:
            # how did this happen?
            self.error("Problem reporting results for %s to %s -- there was nothing to report!" % \
                       (clinic, message.connection.contact))
            message.respond("Sorry, there are no new results for %s." % clinic)
            #            self.waiting_for_pin.pop(message.connection)
            self.pop_pending_connection(message.connection)
        else:
            self.send_results([message.connection], results)
            message.respond(INSTRUCTIONS, name=message.connection.contact.name)

            for res in self.waiting_for_pin[message.connection]:
                res.who_retrieved = message.connection.contact
                res.save()
            self.pop_pending_connection(message.connection)

            # remove pending contacts for this clinic and notify them it
            # was taken care of
            clinic_connections = [contact.default_connection for contact in
                                  Contact.active.filter
                                  (Q(location=clinic) | Q(location__parent=clinic))]

            for conn in clinic_connections:
                if conn in self.waiting_for_pin:
                #                    self.waiting_for_pin.pop(conn)
                    self.pop_pending_connection(conn)
                    OutgoingMessage(conn, RESULTS_PROCESSED,
                                    name=message.connection.contact.name).send()

            self.last_collectors[clinic] = \
                message.connection.contact

    def process_linkage_after_pin(self, message):
        results = self.waiting_for_linkage_pin[message.connection]
        clinic = get_clinic_or_default(message.contact)
        if not results:
            # how did this happen?
            self.error("Problem linking client for %s to %s -- there was nothing to report!" % \
                       (clinic, message.connection.contact))
            message.respond("Sorry, there are no new records to link for %s." % clinic)
            #            self.waiting_for_pin.pop(message.connection)
            self.waiting_for_linkage_pin.pop(message.connection)
        else:
            for res in results:
                OutgoingMessage(message.connection, "Clinical interaction for %(req_id)s confirmed",
                                    # @type res Result
                                    req_id=res.requisition_id).send()
                res.linked = True
                res.save()
            self.waiting_for_linkage_pin.pop(message.connection)

            # remove pending contacts for this clinic and notify them it
#            # was taken care of
#            clinic_connections = [contact.default_connection for contact in
#                                  Contact.active.filter
#                                  (Q(location=clinic) | Q(location__parent=clinic))]

#            for conn in clinic_connections:
#                if conn in self.waiting_for_linkage_pin:
#                #                    self.waiting_for_pin.pop(conn)
#                    self.pop_pending_connection(conn)
#                    OutgoingMessage(conn, " %(name)s has linked",
#                                    name=message.connection.contact.name).send()

#            self.last_collectors[clinic] = \
#                message.connection.contact

    def process_ltc_after_pin(self, message):
        results = self.waiting_for_ltc_pin[message.connection]
        clinic = get_clinic_or_default(message.contact)
        if not results:
            # how did this happen?
            self.error("Problem finding ltc details at %s for %s -- there was nothing to report!" % \
                       (clinic, message.connection.contact))
            message.respond("Sorry, there are no ltc records reday for %s." % clinic)
            #            self.waiting_for_pin.pop(message.connection)
            self.waiting_for_ltc_pin.pop(message.connection)
        else:
            #todo ended here: use send results model
            responses = build_ltc_messages(results)
            for resp in responses:
                message.respond(resp)
            self.waiting_for_ltc_pin.pop(message.connection)

#            self.last_collectors[clinic] = \
#                message.connection.contact

    def send_participant_message(self, res, msgcls=OutgoingMessage):
        conn = self._get_participant_connection(settings.GET_ORIGINAL_TXT(res.phone))
        if conn:
            msgcls(conn, "Your appointment is due at %(clinic)s. If you got this msg by mistake please ignore", clinic=res.clinic.name).send()
            res.participant_informed = res.participant_informed + 1 if res.participant_informed else 1
            res.date_participant_notified = datetime.now()
            res.save()

    def _get_participant_connection(self, phone):
        backend = Backend.objects.get(name__in=["message_tester", "mockbackend"])
        conn = None
        if settings.ON_LIVE_SERVER:
            phone_part = phone[:6]
            preferred_backends = PreferredBackend.objects.filter(phone_first_part=phone_part)
            if preferred_backends:
                conn, _ = Connection.objects.get_or_create(backend=preferred_backends[0].backend, identity=phone)
            else:
                msgs = Message.objects.filter(direction='I', connection__identity__startswith=phone_part).order_by('-date')
                if msgs:
                    backend = msgs[0].connection.backend
                    PreferredBackend.objects.get_or_create(phone_first_part=phone_part, backend=backend)
                    conn, _ = Connection.objects.get_or_create(backend=backend, identity=phone)
        else:
            conn,_ = Connection.objects.get_or_create(backend=backend, identity=phone)
        return conn

    def send_results(self, connections, results, msgcls=OutgoingMessage):
        """Sends the specified results to the given contacts."""
        responses = build_results_messages(results)

        for connection in connections:
            for resp in responses:
                msg = msgcls(connection, resp)
                msg.send()

        for res in results:
            if not res.phone:
                continue
            # @type res Result
            elif not res.send_pii:
                continue
            elif not res.contact_method:
                continue
            elif res.contact_method.lower() != 'sms':
                continue
            self.send_participant_message(res, msgcls)

        for r in results:
            r.notification_status = 'sent'
            r.result_sent_date = datetime.now()
            r.save()

def build_results_messages(results):
    """
    From a list of results, build a list of messages reporting
    their status
    """
    result_strings = []
    max_len = settings.MAX_SMS_LENGTH
    # if messages are updates to requisition ids
    for res in results:
        result_strings.append("**** %s;%s" % (res.requisition_id,
                                              res.get_result_text()))

    result_text, remainder = combine_to_length(result_strings,
                                               length=max_len-len(RESULTS))
    first_msg = RESULTS + result_text
    responses = [first_msg]
    while remainder:
        next_msg, remainder = combine_to_length(remainder)
        responses.append(next_msg)
    return responses


def build_ltc_messages(results):
    result_strings = []
    max_len = settings.MAX_SMS_LENGTH
    # if messages are updates to requisition ids
    for res in results:
        result_strings.append("**** %s %s;%s;%s" % (
        # @type res Result
        settings.GET_ORIGINAL_TEXT(res.fname),
        settings.GET_ORIGINAL_TEXT(res.lname),
        settings.GET_ORIGINAL_TEXT(res.address),
        res.requisition_id))

    result_text, remainder = combine_to_length(result_strings,
                                               length=max_len-len(RESULTS))
    first_msg = "LTC: " + result_text
    responses = [first_msg]
    while remainder:
        next_msg, remainder = combine_to_length(remainder)
        responses.append(next_msg)
    return responses
