'''
Created on Mar 31, 2010

@author: Drew Roos
'''

from datetime import date
from mwana.apps.labresults.models import Result
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
import mwana.apps.labresults.config as config
import rapidsms

RESULTS_READY     = "Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results."
BAD_PIN           = "Sorry, that was not the correct security code. Your security code is a 4-digit number like 1234. If you forgot your security code, reply with keyword 'HELP'"
RESULTS           = "Thank you! Here are your results: "
RESULTS_PROCESSED = "%(name)s has collected these results"
INSTRUCTIONS      = "Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!"

class App (rapidsms.App):
    
    # we store everyone who we think could be sending us a PIN for results 
    # here, so we can intercept the message.
    waiting_for_pin = {}
    
    def start (self):
        """Configure your app in the start phase."""
        self.schedule_notification_task()
        pass
    
    def filter (self, message):
        # this logic goes here to prevent all further processing of the message.
        # because we're not actually generating a response, this prevents the 
        # default app from responding. This is a bit wacky.
        if message.text.strip().upper().startswith("CHECK") \
             and message.connection.contact \
             and message.connection.contact.is_results_receiver:
            # Fake like we need to prompt their clinic for results, as a means 
            # to bypass the scheduler
            self.notify_clinic_pending_results(message.connection.contact.location)
            return True
    
        
    def handle (self, message):
        if message.connection in self.waiting_for_pin:
            pin = message.text.strip()
            if pin.upper() != message.connection.contact.pin.upper():
                message.respond(BAD_PIN)
            else:
                self.send_results(message)
            return True
        
    def send_results (self, message):
        
        results = self.waiting_for_pin[message.connection]
        if not results:
            # how did this happen?
            self.error("Problem reporting results for %s to %s -- there was nothing to report!" % \
                       (message.connection.contact.location, message.connection.contact))
            message.respond("Sorry, there are no new EID results for %s." % message.connection.contact.location)
            self.waiting_for_pin.pop(message.connection)
        else: 
            result_strings = ["Sample %s: %s" % (r.sample_id, r.get_result_display()) \
                              for r in results]
            content = [RESULTS_PROCESSED]
            
            result_text, remainder = combine_to_length(result_strings,
                                                       length=160-len(RESULTS))
            first_msg = RESULTS + result_text
            responses = [first_msg]
            while remainder:
                next_msg, remainder = combine_to_length(remainder)
                responses.append(next_msg)
            
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
                                  Contact.objects.filter\
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
        clinics_with_results = Result.objects.filter(notification_status__in=['new', 'notified'])\
                                .values_list("clinic", flat=True).distinct()
        
        for clinic in clinics_with_results:
            self.notify_clinic_pending_results(clinic)
            
    def notify_clinic_pending_results(self, clinic):
        """Notifies clinic staff that results are ready via sms."""
        messages, results  = self.results_avail_messages(clinic)
        if messages:
            self.send_messages(messages)
            for msg in messages:
                self.waiting_for_pin[msg.connection] = results
            for r in results:
                r.notification_status = 'notified'
                r.save()


    def results_avail_messages(self, clinic):
        results = Result.objects.filter\
                            (clinic=clinic,
                             notification_status__in=['new', 'notified'])
        
        contacts = Contact.objects.filter(location=clinic, is_results_receiver=True)
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

def combine_to_length(list, delimiter=", ", length=160):
    """
    Combine a list of strings to a maximum of a specified length, using the 
    delimiter to separate them.  Returns the combined strings and the 
    remainder as a tuple.
    """
    if not list:  return ("", [])
    if len(list[0]) > length:
        raise Exception("None of the messages will fit in the specified length of %s" % length)
    
    msg = ""
    for i in range(len(list)):
        item = list[i]
        new_msg = item if not msg else msg + delimiter + item
        if len(new_msg) <= length:
            msg = new_msg
        else:
            return (msg, list[i:])
    return (msg, [])
 
def days_ago (d):
    return (date.today() - d).days