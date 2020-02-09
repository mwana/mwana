# vim: ai ts=4 sts=4 et sw=4


from mwana.apps.phia.models import Result, Followup
from mwana.apps.labresults.messages import RESULTS_PROCESSED
from mwana.apps.labresults.messages import NOT_REGISTERED
from mwana.apps.labresults.messages import combine_to_length, BAD_PIN
from rapidsms.messages import OutgoingMessage
from mwana.apps.phia.mocking import MockLtcUtility
import logging
from mwana.apps.labtests.models import PreferredBackend
from rapidsms.contrib.messagelog.models import Message
import mwana.const as const
import rapidsms
from django.db.models import Q
import re


from mwana.apps.phia.mocking import MockResultUtility
from mwana.util import get_clinic_or_default
import mwana.const as const
from mwana.apps.labresults.messages import settings
from mwana.apps.phia.models import Result
from datetime import date
from datetime import datetime
from rapidsms.models import Connection, Backend
from rapidsms.models import Contact
from rapidsms.contrib.scheduler.models import EventSchedule

logger = logging.getLogger(__name__)


RESULTS = "Here are your results: "


class App(rapidsms.apps.base.AppBase):
    # we store everyone who we think could be sending us a PIN for results
    # here, so we can intercept the message.
    waiting_for_pin = {}
    waiting_for_linkage_pin = {}
    waiting_for_demo_results_pin = {}
    waiting_for_ltc_pin = {}
    waiting_for_ltc_visit_pin = {}

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

    LTC_VISIT_REGEX = r"^(?:%s)(?:[\s,;:]+(.+))?$" % ("LTC VISIT")

    def start(self):
        """Configure your app in the start phase."""
        self.schedule_notification_task()
        self.schedule_process_payloads_tasks()
        self.schedule_participant_notification_task()

    def _get_schedule(self, key, default=None):
        schedules = getattr(settings, 'RESULTS160_SCHEDULES', {})
        return schedules.get(key, default)

    def schedule_notification_task(self):
        callback = 'mwana.apps.phia.tasks.send_phia_results_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'hours': [9, 15], 'minutes': [30],
                                        'days_of_week': [0, 1, 2, 3, 4]})
        EventSchedule.objects.create(callback=callback, **schedule)

        callback = 'mwana.apps.phia.tasks.send_tlc_details_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'hours': [10, 14], 'minutes': [30],
                                        'days_of_week': [0, 1, 2, 3, 4]})
        EventSchedule.objects.create(callback=callback, **schedule)

    def schedule_participant_notification_task(self):
        callback = 'mwana.apps.phia.tasks.send_results_ready_notification_to_participant'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'hours': [9, 15], 'minutes': [0],
                                        'days_of_week': [0, 1, 2, 3, 4]})
        EventSchedule.objects.create(callback=callback, **schedule)

    def schedule_process_payloads_tasks(self):
        callback = 'mwana.apps.phia.tasks.process_outstanding_payloads'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'minutes': [0], 'hours': '*'})
        EventSchedule.objects.create(callback=callback, **schedule)

    def notify_clinic_pending_results(self, clinic):

        results = self._pending_results(clinic)
        if not results:
            logger.info("0 results to send for %s" % clinic.name)
            return
        else:
            messages = self.results_avail_messages(clinic, results)
            if messages:
                self.send_messages(messages)
                self._mark_results_pending(results, (msg.connection
                                                     for msg in messages))
                for result in results:
                    result.date_clinic_notified = datetime.now()
                    if not result.date_of_first_notification:
                        result.date_of_first_notification = datetime.now()
                    result.save()

    def notify_clinic_pending_details(self, clinic):
        results = self._pending_ltc(clinic)
        if not results:
            logger.info("0 details to send for %s" % clinic.name)
            return
        else:
            messages = self.details_avail_messages(clinic, results)
            if messages:
                self.send_messages(messages)
                self._mark_details_pending(results, (msg.connection
                                                     for msg in messages))
                 # todo: review
#                for result in results:
#                    result.date_clinic_notified = datetime.now()
#                    if not result.date_of_first_notification:
#                        result.date_of_first_notification = datetime.now()
#                    result.save()

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
        if re.match(self.LTC_VISIT_REGEX, message.text, re.IGNORECASE):
            if not is_eligible_for_phia_results(message.contact):
                message.respond(NOT_REGISTERED)
                return True
            tokens = message.text.split()
            if len(tokens) == 3:
                results = Result.objects.filter(clinic=message.contact.clinic, requisition_id=tokens[2].strip())
                if not results:
                    message.respond("There is no participant with ID %(id)s. Make sure you typed the temporary ID correctly and try again.", id=tokens[2])
                    return True
                self.waiting_for_ltc_visit_pin[message.connection] = results
                message.respond("Please reply with your PIN to save follow-up visit to %(req_id)s", req_id=tokens[2])
            else:
                message.respond("Please specify one valid temporary ID")
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
        elif message.connection in self.waiting_for_ltc_visit_pin \
                and message.connection.contact:
            pin = message.text.strip()
            if pin.upper() == message.connection.contact.pin.upper():
                self.process_ltc_visit_after_pin(message)
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
                message.respond("It looks like you already collected the results/details.")
            else:
                message.respond("It looks like the results/details you are looking for were already collected by %(collector)s. ",
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

    def _mark_details_pending(self, results, connections):
        for connection in connections:
            self.waiting_for_ltc_pin[connection] = results
            #todo: perhaps we should have tc notication status
#        for r in results:
#            r.notification_status = 'notified'
#            r.save()

    def results_avail_messages(self, clinic, results):
        """
        Returns clinic workers registered to receive results notification at this clinic.
        """
        contacts = \
            Contact.active.filter(Q(location=clinic) | Q(location__parent=clinic),
                                  Q(types=const.get_phia_worker_type())).distinct()
        if not contacts:
            self.warning("No contacts registered to receive results at %s! "
                         "These will go unreported until clinic staff "
                         "register at this clinic." % clinic)

        all_msgs = []
        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template="%(clinic)s has %(count)s results ready. Please reply with your pin code to retrieve them.",
                                  clinic=clinic.name, count=results.count())
            all_msgs.append(msg)

        return all_msgs

    def details_avail_messages(self, clinic, results):
        """
        Returns clinic workers registered to receive results notification at this clinic.
        """
        contacts = \
            Contact.active.filter(Q(location=clinic) | Q(location__parent=clinic),
                                  Q(types=const.get_phia_worker_type())).distinct()
        if not contacts:
            self.warning("No contacts registered to receive results at %s! "
                         "These will go unreported until clinic staff "
                         "register at this clinic." % clinic)

        all_msgs = []
        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template="%(clinic)s has %(count)s ALTC participants to link to care. Please reply with your PIN code to get details of ALTC participants.",
                                  clinic=clinic.name, count=results.count())
            all_msgs.append(msg)

        return all_msgs

    def send_messages(self, messages):
        for msg in messages:
            msg.send()

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
            message.respond("Please record these results in your clinic records and promptly delete them from your phone.")

            for res in self.waiting_for_pin[message.connection]:
                res.who_retrieved = message.connection.contact
                res.save()
            self.pop_pending_connection(message.connection)

            # remove pending contacts for this clinic and notify them it
            # was taken care of
            clinic_connections = [contact.default_connection for contact in
                                  Contact.active.filter(location=clinic)]

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

    def process_ltc_visit_after_pin(self, message):
        results = self.waiting_for_ltc_visit_pin[message.connection]
        clinic = get_clinic_or_default(message.contact)
        if not results:
            # how did this happen? 2020/02/07 13:52:59
            self.error("Problem logging follow-up visit for %s to %s -- there was nothing to report!" % \
                       (clinic, message.connection.contact))
            message.respond("Sorry, there are no new records to link for %s." % clinic.name)
            #            self.waiting_for_pin.pop(message.connection)
            self.waiting_for_ltc_visit_pin.pop(message.connection)
        else:
            for res in results:

                Followup.objects.create(clinic_name=message.contact.clinic.name,
                                 reported_by=message.contact.name, result=res,
                                 temp_id=res.requisition_id)

                OutgoingMessage(message.connection, "Follow-up visit to %(req_id)s confirmed",
                                    # @type res Result
                                    req_id=res.requisition_id).send()
                res.save()
            self.waiting_for_ltc_visit_pin.pop(message.connection)

            # remove pending contacts for this clinic and notify them it
#            # was taken care of
#            clinic_connections = [contact.default_connection for contact in
#                                  Contact.active.filter(location=clinic)]
#
#            for conn in clinic_connections:
#                if conn in self.waiting_for_linkage_pin:
#                    self.waiting_for_linkage_pin.pop(conn)
#                    OutgoingMessage(conn, " %(name)s has linked",
#                                    name=message.connection.contact.name).send()
#
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
            responses = build_ltc_messages(results)
            for resp in responses:
                message.respond(resp)
            message.respond("Please record the details in your LTC immediately and DELETE them from your phone. Thank you again!")
            self.waiting_for_ltc_pin.pop(message.connection)

            clinic_connections = [contact.default_connection for contact in
                                  Contact.active.filter(location=clinic)]

            for conn in clinic_connections:
                if conn in self.waiting_for_ltc_pin:
                    self.waiting_for_ltc_pin.pop(conn)
                    OutgoingMessage(conn, "%(name)s has collected LTC details for %(Ids)s",
                    Ids=", ".join(res.requisition_id for res in results),
                                    name=message.connection.contact.name).send()

            self.last_collectors[clinic] = \
                message.connection.contact

#            self.last_collectors[clinic] = \
#                message.connection.contact

    def send_participant_message(self, res, worker=None, msgcls=OutgoingMessage):
        conn = self._get_participant_connection(settings.GET_ORIGINAL_TEXT(res.phone))
        if worker:
            to_see = worker.name
        elif res.who_retrieved:
            to_see = res.who_retrieved.name
        else:
            to_see = "the facility"

        if conn:
#            msgcls(conn, "Your appointment is due at %(clinic)s. If you got this msg by mistake please ignore", clinic=res.clinic.name).send()
            msgcls(conn, "Your results are ready at %(clinic)s, see %(to_see)s with your "
                         "referral form and keep this number %(req_id)s", clinic=res.clinic.name,
                   to_see=to_see,
                   req_id=res.requisition_id).send()
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

    def send_pending_participant_notifications(self):
        results = Result.objects.exclude(who_retrieved=None).exclude(result_sent_date=None).\
            filter(notification_status='sent').filter(date_participant_notified=None)
        for res in results:
            if not res.phone:
                continue
            # @type res Result
            elif not res.send_pii:
                continue
            elif not res.contact_method:
                continue
            elif res.contact_method.strip().lower() != 'sms':
                continue
            self.send_participant_message(res)

    def send_results(self, connections, results, msgcls=OutgoingMessage):
        """Sends the specified results to the given contacts."""
        responses = build_results_messages(results)

        for connection in connections:
            for resp in responses:
                msg = msgcls(connection, resp)
                msg.send()

        for r in results:
            r.notification_status = 'sent'
            r.result_sent_date = datetime.now()
            r.save()

        if len(connections) == 1:
            worker = connections[0].contact

        for res in results:
            if not res.phone:
                continue
            # @type res Result
            elif not res.send_pii:
                continue
            elif not res.contact_method:
                continue
            elif res.contact_method.strip().lower() != 'sms':
                continue
            self.send_participant_message(res, worker, msgcls)



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
        settings.GET_ORIGINAL_TEXT(res.fname) or '',
        settings.GET_ORIGINAL_TEXT(res.lname) or '',
        settings.GET_ORIGINAL_TEXT(res.address) or '',
        res.requisition_id))

    result_text, remainder = combine_to_length(result_strings,
                                               length=max_len-len(RESULTS))
    first_msg = "LTC: " + result_text
    responses = [first_msg]
    while remainder:
        next_msg, remainder = combine_to_length(remainder)
        responses.append(next_msg)
    return responses


def is_eligible_for_phia_results(contact):
    return contact and contact.is_active  and const.get_phia_worker_type() in contact.types.all() \
