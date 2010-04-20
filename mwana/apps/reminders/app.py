#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
import rapidsms
import datetime

from mwana.apps.reminders import models as reminders
from mwana.apps.registration.handlers.register import RegisterHandler


class App(rapidsms.App):
    queryset = reminders.Event.objects.values_list('slug', flat=True)
    
    PATTERN = re.compile(r"^\s*(?P<event_slug>\S+)(?:\s+(?P<date>[\d/-]+))?\s+"
                          "(?P<name>.+)\s*$")
    HELP_TEXT = "To add an event, send <EVENT CODE> <DATE> <NAME>.  The date "\
                "is optional and is logged as TODAY if left out."
    DATE_FORMATS = (
        '%d/%m/%y',
        '%d/%m/%Y',
        '%d/%m',
        '%d-%m-%y',
        '%d-%m-%Y',
        '%d-%m',
    )
    
    def handle(self, msg):
        """
        
        """
        if not msg.contact:
            msg.respond("Sorry you have to register to add events. %s" %
                        RegisterHandler.HELP_TEXT)
            return
        m = self.PATTERN.match(msg.text)
        if m is not None:
            event_slug = m.group('event_slug').strip()
            date_str = (m.group('date') or '').strip()
            name = m.group('name').strip()
            date = None
            
            try:
                event = reminders.Event.objects.get(slug__iexact=event_slug)
            except reminders.Event.DoesNotExist:
                print 'asdfasdfasfdasdf safdasdfasdf NO SUCH EVENT'
                return False
            if date_str:
                for format in self.DATE_FORMATS:
                    try:
                        date = datetime.datetime.strptime(date_str, format)
                    except ValueError:
                        pass
                if not date:
                    msg.respond("Sorry, I couldn't understand that date. "
                                "Please enter the date like so: "
                                "DAY/MONTH/YEAR, for example: 23/04/2010")
                    return
            else:
                date = datetime.datetime.today()
            patient, _ = reminders.Patient.objects.get_or_create(name=name)
            patient.patient_events.create(event=event, date=date)
            msg.respond("Thank you for adding a %(event)s for %(name)s on "
                        "%(date)s.  You will be notified when it's time for "
                        "his or her next appointment.",
                        event=event.name.lower(), 
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
        else:
            msg.respond("Sorry, I didn't understand that. %s" %
                        self.HELP_TEXT)
        return True
