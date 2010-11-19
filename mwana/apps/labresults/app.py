'''
Created on Mar 31, 2010

@author: Drew Roos
'''

from datetime import date, datetime

from django.conf import settings
from django.db.models import Q

from mwana.apps.labresults.messages import *
from mwana.apps.labresults.mocking import MockResultUtility
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.util import is_eligible_for_results
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
import mwana.apps.labresults.config as config
import mwana.const as const
import rapidsms
import re
from mwana.util import get_clinic_or_default
import logging

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):
    
    # we store everyone who we think could be sending us a PIN for results 
    # here, so we can intercept the message.
    waiting_for_pin = {}
    
    # we keep a mapping of locations to who collected last, so we can respond
    # when we receive stale pins
    last_collectors = {}
    
    mocker = MockResultUtility()
    
    # regex format stolen from KeywordHandler
    CHECK_KEYWORD = "CHECK|CHEK|CHEC|CHK"
    CHECK_REGEX   = r"^(?:%s)(?:[\s,;:]+(.+))?$" % (CHECK_KEYWORD)
    
    def start (self):
        """Configure your app in the start phase."""
        self.schedule_change_notification_task()
        self.schedule_notification_task()
        self.schedule_process_payloads_tasks()
        
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
            results = self._pending_results(clinic)
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
                self.send_results(message)
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
                message.respond(SELF_COLLECTED, name=message.connection.contact.name)
            else:
                message.respond(ALREADY_COLLECTED, name=message.connection.contact.name, 
                         collector=self.last_collectors[clinic])
            return True
        return self.mocker.default(message)
        
    def send_results (self, message):
        """
        Sends the actual results in response to the message
        (comes after PIN workflow).
        """
        results = self.waiting_for_pin[message.connection]
        clinic  = get_clinic_or_default(message.contact)
        if not results:
            # how did this happen?
            self.error("Problem reporting results for %s to %s -- there was nothing to report!" % \
                       (clinic, message.connection.contact))
            message.respond("Sorry, there are no new EID results for %s." % clinic)
            self.waiting_for_pin.pop(message.connection)
        else: 
            responses = build_results_messages(results)
            
            for resp in responses: 
                message.respond(resp)

            message.respond(INSTRUCTIONS, name=message.connection.contact.name)
            
            for r in results:
                r.notification_status = 'sent'
                r.result_sent_date = datetime.now()
                r.save()
                
            self.waiting_for_pin.pop(message.connection)
            
            # remove pending contacts for this clinic and notify them it 
            # was taken care of 
            clinic_connections = [contact.default_connection for contact in \
                                  Contact.active.filter\
                                  (location=clinic)]
            
            for conn in clinic_connections:
                if conn in self.waiting_for_pin:
                    self.waiting_for_pin.pop(conn)
                    OutgoingMessage(conn, RESULTS_PROCESSED, 
                                    name=message.connection.contact.name).send()
            
            self.last_collectors[clinic] = \
                        message.connection.contact
        
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
        callback = 'mwana.apps.labresults.tasks.send_results_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'hours': [11], 'minutes': [30],
                                       'days_of_week': [0, 1, 2, 3, 4]})
        EventSchedule.objects.create(callback=callback, **schedule)

    def schedule_change_notification_task(self):
        callback = 'mwana.apps.labresults.tasks.send_changed_records_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'hours': [11], 'minutes': [0],
                                       'days_of_week': [0, 1, 2, 3, 4]})
        EventSchedule.objects.create(callback=callback, **schedule)

    def schedule_process_payloads_tasks(self):
        callback = 'mwana.apps.labresults.tasks.process_outstanding_payloads'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        schedule = self._get_schedule(callback.split('.')[-1],
                                      {'minutes': [0], 'hours': '*'})
        EventSchedule.objects.create(callback=callback, **schedule)

    def notify_clinic_pending_results(self, clinic):
        """Notifies clinic staff that results are ready via sms."""     
        messages, results  = self.results_avail_messages(clinic)
        if messages:
            self.send_messages(messages)
            self._mark_results_pending(results,
                                       (msg.connection for msg in messages))

    def _result_verified(self):
        """
        Only return verified results or results which can't be verified
        due to constraints at the lab.
        """
        return Q(verified__isnull=True) | Q(verified=True)

    def _pending_results(self, clinic):
        """
        Returns the pending results for a clinic. This is limited to 9 results
        (about 3 SMSes) at a time, so clinics aren't overwhelmed with new
        results.
        """
        if settings.SEND_LIVE_LABRESULTS:
            results = Result.objects.filter(clinic=clinic,
                                   notification_status__in=['new', 'notified'])
            return results.filter(self._result_verified())[:9]
        else:
            return Result.objects.none()

    def _updated_results(self, clinic):
        if settings.SEND_LIVE_LABRESULTS:
            results = Result.objects.filter(clinic=clinic,
                                            notification_status='updated')
            return results.filter(self._result_verified())
        else:
            return Result.objects.none()

    def notify_clinic_of_changed_records(self, clinic):
        """Notifies clinic of the new status for changed results."""
        changed_results = []
        updated_results = self._updated_results(clinic)
        if not updated_results:
            return
        for updated_result in updated_results:
            if updated_result.record_change:
                changed_results.append(updated_result)

        if not changed_results:
            return
        contacts = \
        Contact.active.filter(Q(location=clinic)|Q(location__parent=clinic),
                                         Q(types=const.get_clinic_worker_type())).\
                                         order_by('pk')
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
        for r in results:
            r.notification_status = 'notified'
            r.save()

    def results_avail_messages(self, clinic):
        '''
        Returns clinic workers registered to receive results notification at this clinic. 
        '''
        results = self._pending_results(clinic)
        contacts = \
        Contact.active.filter(Q(location=clinic)|Q(location__parent=clinic),
                                         Q(types=const.get_clinic_worker_type()))
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
        
        return all_msgs, results
    
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

    