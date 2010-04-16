#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
import datetime

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location

from mwana.apps.registration.handlers.register import RegisterHandler
from mwana.apps.reminders import models as reminders


class EventHandler(KeywordHandler):
    """
    """

    keyword = "event"

    PATTERN = re.compile(r"\s*(?P<event_slug>\S+)\s+(?P<date>\S+)\s+"
                          "(?P<name>\S+)\s+(?P<location_slug>\S+)\s*$")
    HELP_TEXT = "To add an event, send EVENT <EVENT CODE> <DATE> <NAME> <LOCATION>"
    DATE_FORMATS = (
        '%d/%m/%y',
        '%d/%m/%Y',
        '%d/%m',
        '%d-%m-%y',
        '%d-%m-%Y',
        '%d-%m',
    )
    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond("Sorry you have to register to add events. %s" %
                         RegisterHandler.HELP_TEXT)
            return
        m = self.PATTERN.search(text)
        if m is not None:
            event_slug = m.group('event_slug').strip()
            date_str = m.group('date').strip()
            name = m.group('name').strip()
            location_slug = m.group('location_slug').strip()
            try:
                event = reminders.Event.objects.get(slug__iexact=event_slug)
            except reminders.Event.DoesNotExist:
                self.respond("Sorry, I don't know about an event with code "
                             "%(code)s. Please check your code and try again.",
                             code=event_slug)
                return
            try:
                location = Location.objects.get(slug__iexact=location_slug)
            except Location.DoesNotExist:
                self.respond("Sorry, I don't know about a location with code "
                             "%(code)s. Please check your code and try again.",
                             code=location_slug)
                return
            date = None
            for format in self.DATE_FORMATS:
                try:
                    date = datetime.datetime.strptime(date_str, format)
                except ValueError:
                    pass
            if not date:
                self.respond("Sorry, I couldn't understand that date. Please "
                             "enter the date like so: DAY/MONTH/YEAR, like "
                             "so: 23/04/2010")
                return
            patient, created = reminders.Patient.objects.get_or_create(
                                                  name=name, location=location)
            patient.patient_events.create(event=event, date=date)
            self.respond("Thank you for adding a %(event)s for %(name)s.  You "
                         "will be notified when it's time for his or her next "
                         "appointment.", event=event.name, name=patient.name)
        else:
            self.respond("Sorry, I didn't understand that. %s" %
                         self.HELP_TEXT) 
        