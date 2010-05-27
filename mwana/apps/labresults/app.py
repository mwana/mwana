'''
Created on Mar 31, 2010

@author: Drew Roos
'''

from datetime import date

from django.conf import settings

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

class App (rapidsms.App):
    
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
        
    def schedule_notification_task(self):
        callback = 'mwana.apps.labresults.tasks.send_results_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[12],
                                     minutes=[0])

    def schedule_process_payloads_tasks(self):
        callback = 'mwana.apps.labresults.tasks.process_outstanding_payloads'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours='*', minutes=[0])

    def notify_clinic_pending_results(self, clinic):
        """Notifies clinic staff that results are ready via sms."""
        messages, results  = self.results_avail_messages(clinic)
        if messages:
            self.send_messages(messages)
            self._mark_results_pending(results,
                                       (msg.connection for msg in messages))

    def _pending_results(self, clinic):
        if settings.SEND_LIVE_LABRESULTS:
            return Result.objects.filter(clinic=clinic,
                               notification_status__in=['new', 'notified'])[:9]
        else:
            return Result.objects.none()

    def _mark_results_pending(self, results, connections):
        for connection in connections:
            self.waiting_for_pin[connection] = results
        for r in results:
            r.notification_status = 'notified'
            r.save()

    def results_avail_messages(self, clinic):
        results = self._pending_results(clinic)
        contacts = Contact.active.filter(location=clinic, 
                                         types=const.get_clinic_worker_type())
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

    