from mwana.apps.labtests.messages import PARTICIPANT_RESULTS_READY
import logging
from mwana.apps.labtests.models import PreferredBackend
import mwana.apps.labresults.config as config
import mwana.const as const
import rapidsms
import re
from datetime import date
from datetime import datetime
from django.conf import settings
from django.db.models import Q
from mwana.apps.labtests.messages import *
from mwana.apps.labtests.models import Result
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.util import get_clinic_or_default
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages import OutgoingMessage
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Connection, Backend
from rapidsms.models import Contact

logger = logging.getLogger(__name__)


class App(rapidsms.apps.base.AppBase):
    # we store everyone who we think could be sending us a PIN for results
    # here, so we can intercept the message.
    waiting_for_pin = {}

    # we keep a mapping of locations to who collected last, so we can respond
    # when we receive stale pins
    last_collectors = {}

    # regex format stolen from KeywordHandler
    CHECK_KEYWORD = "VL|blood|viral load|viralLoad"
    CHECK_REGEX = r"^(?:%s)(?:[\s,;:]+(.+))?$" % (CHECK_KEYWORD)

    def start(self):
        """Configure your app in the start phase."""
        self.schedule_notification_task()
        self.schedule_process_payloads_tasks()

    def pop_pending_connection(self, connection):
        self.waiting_for_pin.pop(connection)

    def handle(self, message):
        key = message.text.strip().upper()
        key = key[:4]

        if re.match(self.CHECK_REGEX, message.text, re.IGNORECASE):
            if not is_eligible_for_results(message.connection):
                message.respond(NOT_REGISTERED)
                return True

            clinic = get_clinic_or_default(message.contact)
            # this allows people to check the results for their clinic rather
            # than wait for them to be initiated by us on a schedule
            results = self._pending_results(clinic, True)
            if results:
                message.respond(RESULTS_READY, name=message.contact.name,
                                count=results.count())
                self._mark_results_pending(results, [message.connection])
            else:
                message.respond(NO_RESULTS, name=message.contact.name,
                                clinic=clinic.name)
            return True
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

    def default(self, message):
        # collect our bad pin responses, if they were generated.  See comment
        # in handle()
        logger.warning("in default")
        if hasattr(message, "possible_bad_pin"):
            logger.warning('BAd PIn')
            message.respond("Hello, world!")
#            message.respond(BAD_PIN)
            return True

        # additionally if this is your correct pin then respond that someone
        # has already processed the results (this assumes the only reason
        # you'd ever send your PIN in would be after receiving a notification)
        # This could be more robust, but keeping it simple.
        clinic = get_clinic_or_default(message.contact)
        if is_eligible_for_results(message.connection) \
            and clinic in self.last_collectors \
                and message.text.strip().upper() == message.contact.pin.upper():
            if message.contact == self.last_collectors[clinic]:
                message.respond(SELF_COLLECTED, name=message.connection.contact.name)
            else:
                message.respond(ALREADY_COLLECTED, name=message.connection.contact.name,
                                collector=self.last_collectors[clinic])
            return True

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
            message.respond("Sorry, there are no new viral load results for %s." % clinic)
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
            conn = self._get_participant_connection(res.phone)
            if conn:
                msgcls(conn, PARTICIPANT_RESULTS_READY, clinic=res.clinic.name).send()
                res.participant_informed = res.participant_informed + 1 if res.participant_informed else 1
                res.date_participant_notified = datetime.now()
                res.save()

        for r in results:
            r.notification_status = 'sent'
            r.result_sent_date = datetime.now()
            r.save()

    def chunk_messages(self, content):
        message = ''
        for piece in content:
            message_ext = message + ('; ' if len(message) > 0 else '') + piece

            if len(message_ext) > 140:
                message_ext = piece
                yield message

            message = message_ext

        if len(message) > 0:
            yield message

    def _get_schedule(self, key, default=None):
        schedules = getattr(settings, 'RESULTS160_SCHEDULES', {})
        return schedules.get(key, default)

    def schedule_notification_task(self):
        callback = 'mwana.apps.labtests.tasks.send_results_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'hours': [9, 15], 'minutes': [30],
                                        'days_of_week': [0, 1, 2, 3, 4]})
        EventSchedule.objects.create(callback=callback, **schedule)

    def schedule_process_payloads_tasks(self):
        callback = 'mwana.apps.labtests.tasks.process_outstanding_payloads'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'minutes': [0], 'hours': '*'})
        EventSchedule.objects.create(callback=callback, **schedule)

    def notify_clinic_pending_results(self, clinic):
        """
        If one or more printers are available at the clinic, sends the results
        directly there. Otherwise, notifies clinic staff that results are
        ready via sms.
        """
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

    def _result_verified(self):
        """
        Only return verified results or results which can't be verified
        due to constraints at the lab.
        """
        return Q(verified__isnull=True) | Q(verified=True)

    def _pending_results(self, clinic, check=False):
        """
        Returns the pending results for a clinic. This is limited to 9 results
        (about 3 SMSes) at a time, so clinics aren't overwhelmed with new
        results.
        """
        if settings.SEND_LIVE_LABRESULTS:
            results = Result.objects.filter(clinic=clinic,
                                            clinic__send_live_results=True,
                                            notification_status__in=['new', 'notified'])
            return results.filter(self._result_verified())[:9]
        else:
            return Result.objects.none()

    def _updated_results(self, clinic):
        if settings.SEND_LIVE_LABRESULTS:
            results = Result.objects.filter(clinic=clinic,
                                            clinic__send_live_results=True,
                                            notification_status='updated')
            return results.filter(self._result_verified())
        else:
            return Result.objects.none()

    def printers_for_clinic(self, clinic):
        """ Returns the active printer connections, if any, for a clinic. """
        return Connection.objects.filter(contact__location=clinic,
                                         contact__types=const.get_dbs_printer_type(),
                                         contact__is_active=True)

    def _mark_results_pending(self, results, connections):
        for connection in connections:
            self.waiting_for_pin[connection] = results
        for r in results:
            r.notification_status = 'notified'
            r.save()

    def results_avail_messages(self, clinic, results):
        """
        Returns clinic workers registered to receive results notification at this clinic. 
        """
        contacts = \
            Contact.active.filter(Q(location=clinic) | Q(location__parent=clinic),
                                  Q(types=const.get_clinic_worker_type())).distinct()
        if not contacts:
            self.warning("No contacts registered to receive results at %s! "
                         "These will go unreported until clinic staff "
                         "register at this clinic." % clinic)

        all_msgs = []
        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template=RESULTS_READY,
                                  name=contact.name, count=results.count())
            all_msgs.append(msg)

        return all_msgs

    def no_results_message(self, clinic):
        if clinic.last_fetch == None or days_ago(clinic.last_fetch) >= config.ping_frequency:
            clinic.last_fetch = date.today()
            clinic.save()
            return 'No new viral load results'
        else:
            return None

    def send_messages(self, messages):
        for msg in messages:
            msg.send()

    def _get_participant_connection(self, phone):
        backend = Backend.objects.get(name__in=["message_tester", "mockbackend"])
        conn = None
        if settings.ON_LIVE_SERVER:
            phone_part = phone[:6]
            backends = PreferredBackend.objects.filter(phone_first_part=phone_part)
            if backends:
                conn, _ = Connection.objects.get_or_create(backend=backends[0], identity=phone)
            else:
                msgs = Message.objects.filter(direction='I', connection__identity__startswith=phone_part).order_by('-date')
                if msgs:
                    backend = [0].connection.backend
                    PreferredBackend.objects.get_or_create(phone_first_part=phone_part, backend=backend)
                    conn, _ = Connection.objects.get_or_create(backend=backend, identity=phone)
        else:
            conn,_ = Connection.objects.get_or_create(backend=backend, identity=phone)
        return conn


def days_ago(d):
    return (date.today() - d).days
