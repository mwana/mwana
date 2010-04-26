#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
import rapidsms
import datetime

from rapidsms.models import Contact
from rapidsms.contrib.scheduler.models import EventSchedule, ALL

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.reminders import models as reminders
from mwana.apps.reminders.handlers.agent import AgentHelper


class App(rapidsms.App):
    queryset = reminders.Event.objects.values_list('slug', flat=True)
    
    PATTERN = re.compile(r"^\s*(?P<event_slug>\S+)(?:\s+(?P<date>[\d/ -]+))?\s+"
                          "(?P<name>.+)\s*$")
    HELP_TEXT = "To add a %(event_lower)s, send %(event_upper)s <DATE> <NAME>."\
                " The date is optional and is logged as TODAY if left out."
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

    def start(self):
        self.schedule_notification_task()
        pass
    
    def schedule_notification_task (self):
        callback = 'mwana.apps.reminders.tasks.send_notifications'
        
        #remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, minutes=ALL)

    def _parse_date(self, date_str):
        date = None
        for format in self.DATE_FORMATS:
            try:
                date = datetime.datetime.strptime(date_str, format)
            except ValueError:
                pass
        if date:
            # is there a better way to do this? if no year was specified in
            # the string, it defaults to 1900
            if date.year == 1900:
                date = date.replace(year=datetime.datetime.now().year)
        return date

    def _patient_type(self):
        try:
            return ContactType.objects.get(slug='patient')
        except ContactType.DoesNotExist:
            return ContactType.objects.create(name='Patient',
                                              slug='patient')

    def handle(self, msg):
        """
        Handles the actual adding of events.  Other simpler commands are done
        through handlers.
        
        This needs to be an app because the "keywords" for this command are
        dynamic (i.e., in the database) and, while it's possible to make a
        handler with dynamic keywords, the API doesn't give you a way to see
        what keyword was actually typed by the user.
        """
        
        event_slug = msg.text.split()[0]
        try:
            event = reminders.Event.objects.get(slug__iexact=event_slug)
        except reminders.Event.DoesNotExist:
            return False
        
        m = self.PATTERN.match(msg.text)
        if m is not None:
            date_str = (m.group('date') or '').strip()
            name = m.group('name').strip()

            # parse the date
            if date_str:
                date = self._parse_date(date_str)
                if not date:
                    msg.respond("Sorry, I couldn't understand that date. "
                                "Please enter the date like so: "
                                "DAY MONTH YEAR, for example: 23 04 2010")
                    return
            else:
                date = datetime.datetime.today()

            # fetch or create the patient
            if msg.contact.location and msg.contact.zone_code is not None:
                patient, _ = Contact.objects.get_or_create(
                                            name=name,
                                            location=msg.contact.location,
                                            zone_code=msg.contact.zone_code)
            else:
                patient = Contact.objects.create(name=name)

            # make sure the contact has the correct type (patient)
            patient_t = self._patient_type()
            if not patient.types.filter(pk=patient_t.pk).count():
                patient.types.add(patient_t)

            # make sure we don't create a duplicate patient event
            if patient.patient_events.filter(event=event, date=date).count():
                msg.respond("Sorry, but someone has already registered a "
                            "%(event)s for %(name)s on %(date)s.",
                            event=event.name.lower(), name=patient.name,
                            date=date.strftime('%d/%m/%Y'))
                return
            patient.patient_events.create(event=event, date=date,
                                          cba_conn=msg.connection)
            gender = event.possessive_pronoun
            msg.respond("You have successfully registered a %(event)s for "
                        "%(name)s on %(date)s. You will be notified when "
                        "it is time for %(gender)s next appointment at the "
                        "clinic.", event=event.name.lower(), gender=gender,
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
        else:
            msg.respond("Sorry, I didn't understand that. " +
                        self.HELP_TEXT % {'event_lower': event.name.lower(),
                                          'event_upper': event.name.upper()})
        return True
