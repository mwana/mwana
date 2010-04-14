import rapidsms

'''
Created on Mar 31, 2010

@author: Drew Roos
'''

import rapidsms
import logging
from labresults.models import *
import labresults.config as config
from scheduler.models import set_daily_event, EventSchedule
import messaging.app

class App (rapidsms.app.App):

    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle (self, message):
        pass
    
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
        
