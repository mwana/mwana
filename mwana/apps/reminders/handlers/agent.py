#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
import re

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.reminders import models as reminders


class AgentHelper(KeywordHandler):
    """
    """

    keyword = "agent"

    PATTERN = re.compile(r"^\s*(?P<clinic>\S+)\s+(?P<zone>\d+)\s+(?P<name>.+)$")
    HELP_TEXT = "To register as a RemindMi agent, send AGENT <CLINIC CODE> <ZONE #> <YOUR NAME>"
    
    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        m = self.PATTERN.search(text)
        if m is not None:
            location_slug = m.group('clinic').strip()
            zone = m.group('zone').strip()
            name = m.group('name').strip()
            try:
                location = Location.objects.get(slug__iexact=location_slug)
                contact = Contact.objects.create(name=name, location=location,
                                                 zone_code=zone)
                try:
                    cba_t = ContactType.objects.get(slug='cba')
                except ContactType.DoesNotExist:
                    cba_t = ContactType.objects.create(name='Community Based Agents',
                                                       slug='cba')
                contact.types.add(cba_t)
                self.msg.connection.contact = contact
                self.msg.connection.save()
                events = list(reminders.Event.objects.values_list('slug',
                                                                  flat=True))
                if len(events) == 2:
                    events = ' or '.join(events)
                elif len(events) > 0:
                    if len(events) > 2:
                        events[-1] = 'or %s' % event[-1]
                    events = ', '.join(events)
                if events:
                    notify_text = " Please notify us next time there is a "\
                                  "%s in your zone." % events
                else:
                    notify_text = ""
                self.respond("Thank you %(name)s! You have successfully "
                             "registered at as a RemindMi Agent for "
                             "%(location)s.%(notify_text)s",
                             name=contact.name, location=location.name,
                             notify_text=notify_text)
            except Location.DoesNotExist:
                self.respond("Sorry, I don't know about a location with code %(code)s. Please check your code and try again.",
                             code=location_slug)
        else:
            self.respond("Sorry, I didn't understand that. Make sure you send your clinic, zone #, and name like: AGENT <CLINIC CODE> <ZONE #> <YOUR NAME>") 
