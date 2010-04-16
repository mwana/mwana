'''
Created on Mar 31, 2010

@author: Drew Roos
'''

import rapidsms
import logging
from mwana.apps.labresults.models import *
import mwana.apps.labresults.config as config
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages import OutgoingMessage
from datetime import date

class App (rapidsms.App):

    def start (self):
        """Configure your app in the start phase."""
        self.schedule_notification_task()
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle (self, message):
        if message.text.startswith('results'):
            try:
                recipient = Recipient.objects.get(connection=message.connection)
            except Recipient.DoesNotExist:
                send(message.connection, 'Do not recognize phone number')

            pieces = message.text.split()
            if len(pieces) < 2:
                send(message.connection, 'Missing PIN')

            pin = pieces[1]
            if pin.upper() != recipient.pin.upper():
                send(message.connection, 'PIN is wrong')

            clinic = recipient.clinic_id
            self.send_results(clinic, recipient.connection)
            clinic.last_fetch = date.now()
            clinic.save()
        
            return True
        else:
            return False
    
    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass
        
    def send_results (self, clinic, conn):
        outcomes = {'P': 'POS', 'N': 'NEG', 'B': 'BAD'}
        
        results = Result.objects.filter(notification_status__in=['new', 'notified'], clinic_id=clinic)
        
        content = []
        content.append('%d %s' % (len(results), 'results' if len(results) > 1 else 'result'))
        for r in results:
            content.append('%s (%s) %s' % (r.patient_id, r.sample_id, outcomes[r.result]))
        content.append('Record these results in the logbook, then delete these messages and the message you sent')
        
        for sms in self.chunk_messages(content):
            send(conn, sms)
            
        for r in results:
            r.notification_status = 'sent'
            r.save()
        
    def chunk_messages(self, content):
        message = ''
        for piece in content:
            message_ext = message + ('; ' if len(message) > 0 else '') + piece
            
            if len(message_ext) > 140:
                message_ext = piece
                yield message
            
            message = message_ext
        
    def schedule_notification_task (self):
        callback = 'mwana.apps.labresults.app.send_results_notification'
        
        #remove existing schedule tasks; reschedule based on the current setting from config
        try:
            EventSchedule.objects.filter(callback=callback).delete()
        except EventSchedule.DoesNotExist:
            pass
        
        task = EventSchedule(callback=callback, **config.sched)
        task.save()
        
    def send_results_notification (self):
        results = Result.objects.filter(notification_status__in=['new', 'notified'])
        clinics = Clinic.objects.all()

        message_queue = []

        for clinic in clinics:
            unsent_results = [r for r in results if r.clinic_id == clinic]
            if len(unsent_results) > 0:
                message = self.results_avail_message(unsent_results, clinic)
            else:
                message = self.no_results_message(clinic)
            
            if message != None:
                message_queue.append((clinic, message))
                
        self.send_messages(message_queue)
        
        for r in results:
            r.notification_status = 'notified'
            r.save()
        
    def results_avail_message (self, unsent_results, clinic):
        count = len(unsent_results)
        already_notified_results = [r for r in unsent_results if r.notification_status == 'notified']
        
        msg = '%d DBS %s available' % (count, 'results' if count > 1 else 'result')
        if len(already_notified_results) > 0:
            earliest_notified = min([r.entered_on for r in already_notified_results])
            unfetched_results_since = days_ago(earliest_notified) + 1
            if days_ago > 1:
                msg += ' from the last %d days' % unfetched_results_since
        
        msg += '. Text \'results [your PIN]\' to retrieve'
        
        return msg
    
    def no_results_message (self, clinic):
        if clinic.last_fetch == None or days_ago(clinic.last_fetch) >= config.ping_frequency:
            clinic.last_fetch = date.today()
            clinic.save()
            return 'No new DBS results'
        else:
            return None

    def send_messages (self, messages):
        for (clinic, message) in messages:
            recipients = Recipient.objects.filter(clinic_id=clinic)
            for rcp in recipients:
                send(rcp.connection, message)
    
def send (conn, text):
    OutgoingMessage(connection=conn, text=text).send()
    
def days_ago (d):
    return (date.today() - d).days