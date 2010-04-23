#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
import rapidsms
import datetime

from rapidsms.models import Contact

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.reminders import models as reminders
from mwana.apps.reminders.handlers.agent import AgentHelper


class App(rapidsms.App):
    queryset = reminders.Event.objects.values_list('slug', flat=True)
    
    PATTERN = re.compile(r"^\s*(?P<event_slug>\S+)(?:\s+(?P<date>[\d/ -]+))?\s+"
                          "(?P<name>.+)\s*$")
    HELP_TEXT = "To add an event, send <EVENT CODE> <DATE> <NAME>.  The date "\
                "is optional and is logged as TODAY if left out."
    DATE_FORMATS = (
        '%d %m %y',
        '%d %m %Y',
        '%d %m',
        '%d/%m/%y',
        '%d/%m/%Y',
        '%d/%m',
        '%d-%m-%y',
        '%d-%m-%Y',
        '%d-%m',
    )
    
    def handle(self, msg):
        """
        Handles the actual adding of events.  Other simpler commands are done
        through handlers.
        
        This needs to be an app because the "keywords" for this command are
        dynamic (i.e., in the database) and, while it's possible to make a
        handler with dynamic keywords, the API doesn't give you a way to see
        what keyword was actually typed by the user.
        """
        m = self.PATTERN.match(msg.text)
        if m is not None:
            event_slug = m.group('event_slug').strip()
            date_str = (m.group('date') or '').strip()
            name = m.group('name').strip()
            date = None
            
            try:
                event = reminders.Event.objects.get(slug__iexact=event_slug)
            except reminders.Event.DoesNotExist:
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
                                "DAY MONTH YEAR, for example: 23 04 2010")
                    return
                else:
                    # is there a better way to do this?
                    if date.year == 1900:
                        date.year = datetime.datetime.now().year
            else:
                date = datetime.datetime.today()
            if msg.contact.location and msg.contact.zone_code is not None:
                patient, _ = Contact.objects.get_or_create(
                                            name=name,
                                            location=msg.contact.location,
                                            zone_code=msg.contact.zone_code)
            else:
                patient = Contact.objects.create(name=name)
            try:
                patient_t = ContactType.objects.get(slug='patient')
            except ContactType.DoesNotExist:
                patient_t = ContactType.objects.create(name='Patient',
                                                       slug='patient')
            patient.types.add(patient_t)
            patient.patient_events.create(event=event, date=date,
                                          cba_conn=msg.connection)
            gender = event.possessive_pronoun
            msg.respond("You have successfully registered a %(event)s for "
                        "%(name)s on %(date)s. You will be notified when "
                        "it is time for %(gender)s next appointment at the "
                        "clinic.", event=event.name.lower(), gender=gender,
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
        else:
            msg.respond("Sorry, I didn't understand that. %s" %
                        self.HELP_TEXT)
        return True
