# vim: ai ts=4 sts=4 et sw=4
'''
Created on Mar 31, 2010

@author: Drew Roos
'''

import logging
import mwana.apps.labresults.config as config
import mwana.const as const
import rapidsms
import re
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from mwana.apps.labresults.messages import *
from mwana.apps.labresults.mocking import MockResultUtility
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.models import PendingPinConnections
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.apps.tlcprinters.messages import TLCOutgoingMessage
from mwana.util import get_clinic_or_default
from mwana.locale_settings import SYSTEM_LOCALE, LOCALE_ZAMBIA, LOCALE_MALAWI
# from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Connection
from rapidsms.models import Contact

logger = logging.getLogger(__name__)


class App (rapidsms.apps.base.AppBase):

    # we store everyone who we think could be sending us a PIN for results
    # here, so we can intercept the message.
    waiting_for_pin = {}

    # we keep a mapping of locations to who collected last, so we can respond
    # when we receive stale pins
    last_collectors = {}
    for record in PendingPinConnections.objects.filter():
            if record.connection in waiting_for_pin.keys():
                waiting_for_pin[record.connection].append(record.result)
            else:
                waiting_for_pin[record.connection] = [record.result]

    mocker = MockResultUtility()

    # regex format stolen from KeywordHandler
    CHECK_KEYWORD = "CHECK|CHEK|CHEC|CHK"
    CHECK_REGEX = r"^(?:%s)(?:[\s,;:]+(.+))?$" % (CHECK_KEYWORD)

    # def start (self):
        # """Configure your app in the start phase."""
        # self.schedule_change_notification_task()
        # self.schedule_notification_task()
        # self.schedule_process_payloads_tasks()
        # self.schedule_send_results_to_printer_task()

    def pop_pending_connection(self,connection):
        self.waiting_for_pin.pop(connection)
        PendingPinConnections.objects.filter(connection=connection).delete()

    def handle (self, message):
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
                message.respond(RESULTS_READY % dict(name=message.contact.name,
                                                     count=results.count()))
                self._mark_results_pending(results, [message.connections[0]])
            else:
                message.respond(NO_RESULTS % dict(name=message.contact.name,
                                                  clinic=clinic.name))
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

        # Finally, check if our mocker wants to do anything with this message,
        # and notify the router if so.
        elif self.mocker.handle(message):
            return True

    def default(self, message):
        # collect our bad pin responses, if they were generated.  See comment
        # in handle()
        if hasattr(message, "possible_bad_pin"):
            message.respond(BAD_PIN)
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
                    message.respond(SELF_COLLECTED % dict(
                        name=message.connection.contact.name))
                else:
                    message.respond(ALREADY_COLLECTED % dict(
                        name=message.connection.contact.name,
                        collector=self.last_collectors[clinic]))
                return True
        return self.mocker.default(message)

    def send_results_after_pin (self, message):
        """
        Sends the actual results in response to the message
        (comes after PIN workflow).
        """
        results = self.waiting_for_pin[message.connection]
        clinic  = get_clinic_or_default(message.contact)
        if not results:
            # how did this happen?
            logger.error("Problem reporting results for %s to %s -- there was nothing to report!" % \
                       (clinic, message.connection.contact))
            message.respond("Sorry, there are no new EID results for %s." % clinic)
#            self.waiting_for_pin.pop(message.connection)
            self. pop_pending_connection(message.connection)
        else:
            self.send_results([message.connection], results)
            message.respond(INSTRUCTIONS % dict(
                name=message.connection.contact.name))

#            self.waiting_for_pin.pop(message.connection)
            self. pop_pending_connection(message.connection)

            # remove pending contacts for this clinic and notify them it
            # was taken care of
            clinic_connections = [contact.default_connection for contact in \
                Contact.active.filter\
                (Q(location=clinic) | Q(location__parent=clinic))]

            for conn in clinic_connections:
                if conn in self.waiting_for_pin:
#                    self.waiting_for_pin.pop(conn)
                    self. pop_pending_connection(conn)
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

        for r in results:
            r.notification_status = 'sent'
            r.result_sent_date = datetime.now()
            r.save()

    def send_printer_results(self, connections, results, msgcls=OutgoingMessage):
        """Sends the specified results to the given contacts."""
        responses = build_printer_results_messages(results)

        for connection in connections:
            for resp in responses:
                msg = msgcls(connection, resp)
                msg.send()
                # if SYSTEM_LOCALE == LOCALE_MALAWI:
                    # time.sleep(2)

        for r in results:
            r.notification_status = 'sent'
            r.result_sent_date = datetime.now()
            r.save()

        clinic = results[0].clinic
        contacts = Contact.active.filter(Q(location=clinic) |
                                         Q(location__parent=clinic),
                                         Q(types=const.get_clinic_worker_type())
                                         ).distinct().order_by('pk')
        if SYSTEM_LOCALE == LOCALE_MALAWI:
            NUIDs = ", ".join(
                [str(r.requisition_id) if len(str(r.requisition_id)) > 9 else
                 str(r.clinic_care_no) for r in results])
        else:
            NUIDs = ", ".join(str(res.requisition_id) for res in results)
        for contact in contacts:
            msg_text = (u"Hello {name}, {count} results sent to printer "
                        u"at {clinic}. IDs : {nuids}"
                        u"".format(name=contact.name, count=len(results),
                        clinic=clinic.name, nuids=NUIDs))
            OutgoingMessage(contact.default_connection, msg_text).send()


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

    # def _get_schedule(self, key, default=None):
    #     schedules = getattr(settings, 'RESULTS160_SCHEDULES', {})
    #     return schedules.get(key, default)

    # def schedule_notification_task(self):
    #     callback = 'mwana.apps.labresults.tasks.send_results_notification'
    #     # remove existing schedule tasks; reschedule based on the current setting
    #     EventSchedule.objects.filter(callback=callback).delete()
    #     schedule = self._get_schedule(callback.split('.')[-1],
    #                                   {'hours': [11], 'minutes': [30],
    #                                   'days_of_week': [0, 1, 2, 3, 4]})
    #     EventSchedule.objects.create(callback=callback, ** schedule)

    # def schedule_change_notification_task(self):
    #     callback = 'mwana.apps.labresults.tasks.send_changed_records_notification'
    #     # remove existing schedule tasks; reschedule based on the current setting
    #     EventSchedule.objects.filter(callback=callback).delete()
    #     schedule = self._get_schedule(callback.split('.')[-1],
    #                                   {'hours': [11], 'minutes': [0],
    #                                   'days_of_week': [0, 1, 2, 3, 4]})
    #     EventSchedule.objects.create(callback=callback, ** schedule)

    # def schedule_process_payloads_tasks(self):
    #     callback = 'mwana.apps.labresults.tasks.process_outstanding_payloads'
    #     # remove existing schedule tasks; reschedule based on the current setting
    #     EventSchedule.objects.filter(callback=callback).delete()
    #     schedule = self._get_schedule(callback.split('.')[-1],
    #                                   {'minutes': [0], 'hours': '*'})
    #     EventSchedule.objects.create(callback=callback, ** schedule)

    # def schedule_send_results_to_printer_task(self):
    #     callback = 'mwana.apps.labresults.tasks.send_results_to_printer'
    #     # remove existing schedule tasks; reschedule based on the current setting
    #     EventSchedule.objects.filter(callback=callback).delete()
    #     EventSchedule.objects.create(callback=callback, hours=[8, 10, 14, 16], minutes=[50],
    #                                  days_of_week=[0, 1, 2, 3, 4])

    def notify_clinic_pending_results(self, clinic):
        """
        If one or more printers are available at the clinic, sends the results
        directly there. Otherwise, notifies clinic staff that results are
        ready via sms.
        """
        printers = self.printers_for_clinic(clinic)
        if SYSTEM_LOCALE == LOCALE_MALAWI and printers.exists():
            results = self._pending_results(clinic, to_printer=True)
        else:
            results = self._pending_results(clinic)
        if not results:
            logger.info("0 results to send for %s" % clinic.name)
            return

        if printers.exists():
            self.send_printer_results(printers, results, msgcls=TLCOutgoingMessage)
        else:
            messages  = self.results_avail_messages(clinic, results)
            if messages:
                self.send_messages(messages)
                self._mark_results_pending(results, (msg.connection
                                       for msg in messages))

    def send_printers_pending_results(self, clinic):
        """
        Sends new results to printers at clinics.
        """
        if SYSTEM_LOCALE == LOCALE_MALAWI:
            results = self._pending_results(clinic, True, True)
        else:
            results = self._pending_results(clinic, True)
        printers = self.printers_for_clinic(clinic)
        if printers.exists():
            self.send_printer_results(printers, results, msgcls=TLCOutgoingMessage)

    def _result_verified(self):
        """
        Only return verified results or results which can't be verified
        due to constraints at the lab.
        """
        return Q(verified__isnull=True) | Q(verified=True)

    def _pending_results(self, clinic, check=False, to_printer=False):
        """
        Returns the pending results for a clinic. This is limited to 9 results
        (about 3 SMSes) at a time, so clinics aren't overwhelmed with new
        results.
        """
        if settings.SEND_LIVE_LABRESULTS:
            results = Result.objects.filter(clinic=clinic,
                                            clinic__send_live_results=True,
                                            notification_status__in=['new', 'notified'])
            results = self.filterout(results, check)
            if SYSTEM_LOCALE == LOCALE_MALAWI and to_printer:
                return results.filter(self._result_verified())
            else:
                return results.filter(self._result_verified())[:9]
        else:
            return Result.objects.none()


    def filterout(self, results, check):
        """
        If clinic has not been retrieving results despite being notified, then
        send them only once a week
        """

        today = datetime.today()
        ago = today - timedelta(days=7)
        if SYSTEM_LOCALE == LOCALE_ZAMBIA and not check:
            if today.weekday() != 0:
                results = results.exclude(notification_status='notified',
                arrival_date__lte=ago)
        return results

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

    def notify_clinic_of_changed_records(self, clinic):
        """
        Notifies clinic of the new status for changed results.
        """
        changed_results = []
        updated_results = self._updated_results(clinic)
        if not updated_results:
            return
        for updated_result in updated_results:
            if updated_result.record_change:
                changed_results.append(updated_result)

        if not changed_results:
            return

        # if a printer exists for this clinic, send the results
        # straight there.
        printers = self.printers_for_clinic(clinic)
        if printers.exists():
            self.send_printer_results(printers, changed_results,
                          msgcls=TLCOutgoingMessage)
            return

        contacts = \
        Contact.active.filter(Q(location=clinic) | Q(location__parent=clinic),
                              Q(types=const.get_clinic_worker_type())).\
            distinct().order_by('pk')
        if not contacts:
            self.warning("No contacts registered to receive results at %s! "
                         "These will go unreported until clinic staff "
                         "register at this clinic." % clinic)
            return

        RESULTS_CHANGED     = "URGENT: A result sent to your clinic has changed. Please send your pin, get the new result and update your logbooks."
        if len(changed_results) > 1:
            RESULTS_CHANGED     = "URGENT: Some results sent to your clinic have changed. Please send your pin, get the new results and update your logbooks."

        all_msgs = []
        help_msgs = []

        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template=RESULTS_CHANGED)
            all_msgs.append(msg)

        contact_details = []
        for contact in contacts:
            contact_details.append("%s:%s" % (contact.name, contact.default_connection.identity))

        if all_msgs:
            self.send_messages(all_msgs)
            self._mark_results_pending(changed_results,
                                       (msg.connection for msg in all_msgs))

            for help_admin in Contact.active.filter(is_help_admin=True):
                h_msg = OutgoingMessage(
                                        help_admin.default_connection,
                                        "Make a followup for changed results %s: %s. Contacts = %s" %
                                        (clinic.name, ";****".join("ID=" + res.requisition_id + ", Result="
                                        + res.result + ", old value=" + res.old_value for res in changed_results),
                                        ", ".join(contact_detail for contact_detail in contact_details))
                                        )
                help_msgs.append(h_msg)
            if help_msgs:
                self.send_messages(help_msgs)
                logger.info("sent following message to help admins: %s" % help_msgs[0].text)
            else:
                logger.info("There are no help admins")



    def _mark_results_pending(self, results, connections):
        for connection in connections:
            self.waiting_for_pin[connection] = results
            for res in results:
                PendingPinConnections.objects.create(connection=connection, result=res)
        for r in results:
            r.notification_status = 'notified'
            r.save()

    def results_avail_messages(self, clinic, results):
        '''
        Returns clinic workers registered to receive results notification at this clinic.
        '''
        contacts = \
        Contact.active.filter(Q(location=clinic) | Q(location__parent=clinic),
            Q(types=const.get_clinic_worker_type())).distinct()
        if not contacts:
            self.warning("No contacts registered to receiver results at %s! "
                         "These will go unreported until clinic staff "
                         "register at this clinic." % clinic)

        all_msgs = []
        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template=RESULTS_READY,
                                  name=contact.name, count=results.count())
            all_msgs.append(msg)

        return all_msgs

    def no_results_message (self, clinic):
        if clinic.last_fetch == None or days_ago(clinic.last_fetch) >= config.ping_frequency:
            clinic.last_fetch = date.today()
            clinic.save()
            return 'No new DBS results'
        else:
            return None

    def send_messages (self, messages):
        for msg in messages:  msg.send()

def days_ago (d):
    return (date.today() - d).days
