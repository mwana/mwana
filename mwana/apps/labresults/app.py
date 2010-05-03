'''
Created on Mar 31, 2010

@author: Drew Roos
'''

from datetime import date
from mwana.apps.labresults.mocking import MockResultUtility
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.messages import *
import mwana.const as const
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
import mwana.apps.labresults.config as config
import rapidsms

class App (rapidsms.App):
    
    # we store everyone who we think could be sending us a PIN for results 
    # here, so we can intercept the message.
    waiting_for_pin = {}
    mocker = MockResultUtility()
    
    def start (self):
        """Configure your app in the start phase."""
        # this breaks on postgres
        # self.schedule_notification_task()
        
    def handle (self, message):
        key = message.text.strip().upper()
        key =key[:4]
        if key in "CHECKCHEK":
            if not message.connection.contact or \
               not const.get_clinic_worker_type() in \
               message.connection.contact.types.all():
                message.respond(NOT_REGISTERED)
                return True
            
            # this allows people to check the results for their clinic rather
            # than wait for them to be initiated by us on a schedule
            results = Result.objects.filter(
                            clinic=message.contact.location,
                            notification_status__in=['new', 'notified'])
            if results:
                message.respond(RESULTS_READY, name=message.contact.name,
                                count=results.count())
                self._mark_results_pending(results, [message.connection])
            else:
                message.respond(NO_RESULTS, name=message.contact.name,
                                clinic=message.contact.location.name)
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
        return self.mocker.default(message)
        
    def send_results (self, message):
        """
        Sends the actual results in response to the message
        (comes after PIN workflow).
        """
        results = self.waiting_for_pin[message.connection]
        if not results:
            # how did this happen?
            self.error("Problem reporting results for %s to %s -- there was nothing to report!" % \
                       (message.connection.contact.location, message.connection.contact))
            message.respond("Sorry, there are no new EID results for %s." % message.connection.contact.location)
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
                                  (location=message.connection.contact.location)]
            
            for conn in clinic_connections:
                if conn in self.waiting_for_pin:
                    self.waiting_for_pin.pop(conn)
                    OutgoingMessage(conn, RESULTS_PROCESSED, 
                                    name=message.connection.contact.name).send()
                                    
        
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
        
    def schedule_notification_task (self):
        callback = 'mwana.apps.labresults.app.send_results_notification'
        
        #remove existing schedule tasks; reschedule based on the current setting from config
        try:
            EventSchedule.objects.filter(callback=callback).delete()
        except EventSchedule.DoesNotExist:
            pass
        
        task = EventSchedule(callback=callback, days_of_month='*', hours=[8], minutes=[0]) #**config.sched)
        task.save()
        
    def send_results_notification (self):
        clinics_with_results =\
          Result.objects.filter(notification_status__in=['new', 'notified'])\
                                .values_list("clinic", flat=True).distinct()
        
        for clinic in clinics_with_results:
            self.notify_clinic_pending_results(clinic)
            
    def notify_clinic_pending_results(self, clinic):
        """Notifies clinic staff that results are ready via sms."""
        messages, results  = self.results_avail_messages(clinic)
        if messages:
            self.send_messages(messages)
            self._mark_results_pending(results, (msg.connection for msg in messages))

    def _mark_results_pending(self, results, connections):
        for connection in connections:
            self.waiting_for_pin[connection] = results
        for r in results:
            r.notification_status = 'notified'
            r.save()

    def results_avail_messages(self, clinic):
        results = Result.objects.filter\
                            (clinic=clinic,
                             notification_status__in=['new', 'notified'])
        
        contacts = Contact.active.filter(location=clinic, 
                                         types=const.get_clinic_worker_type())
        if not contacts:
            self.error("No contacts registered to receiver results at %s! These will go unreported." % clinic)
        
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

    
    