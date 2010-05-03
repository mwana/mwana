#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
import re

from mwana.apps.reminders import models as reminders
from mwana import const


class AgentHelper(KeywordHandler):
    """
    """

    keyword = "agent|agemt|urgent|ajent|agdmt|agnt|agant"

    PATTERN = re.compile(r"^\s*(?P<clinic>\S+)\s+(?P<zone>\S+)\s+(?P<name>.+)$")
    HELP_TEXT = "To register as a RemindMi agent, send AGENT <CLINIC CODE> "\
                "<ZONE #> <YOUR NAME>"
    
    def help(self):
        self.respond(self.HELP_TEXT)

    def _get_notify_text(self):
        events = list(reminders.Event.objects.values_list('slug', flat=True))
        if len(events) == 2:
            events = ' or '.join(events)
        elif len(events) > 0:
            if len(events) > 2:
                events[-1] = 'or %s' % events[-1]
            events = ', '.join(events)
        if events:
            notify_text = " Please notify us next time there is a "\
                          "%s in your zone." % events
        else:
            notify_text = ""
        return notify_text

    def _get_or_create_zone(self, clinic, name):
        # create the zone if it doesn't already exist
        zone_type = const.get_zone_type()
        try:
            # get_or_create does not work with iexact
            zone = Location.objects.get(name__iexact=name,
                                        parent=clinic,
                                        type=zone_type)
        except Location.DoesNotExist:
            zone = Location.objects.create(name=name,
                                           parent=clinic,
                                           slug=get_unique_value(Location.objects, "slug", name),
                                           type=zone_type)
        return zone

    def handle(self, text):
        m = self.PATTERN.search(text)
        if m is not None:
            clinic_slug = m.group('clinic').strip()
            zone_slug = m.group('zone').strip()
            name = m.group('name').strip().title()
            # require the clinic to be pre-populated
            try:
                clinic = Location.objects.get(slug__iexact=clinic_slug,
                                             type__slug__in=const.CLINIC_SLUGS)
            except Location.DoesNotExist:
                self.respond("Sorry, I don't know about a clinic with code "
                             "%(code)s. Please check your code and try again.",
                             code=clinic_slug)
                return
            zone = self._get_or_create_zone(clinic, zone_slug)
            if self.msg.contact is not None and\
               self.msg.contact.location == zone:
                self.respond("Hello %(name)s! You are already registered as "
                             "a RemindMi Agent for zone %(zone)s of %(clinic)s.", 
                             name=self.msg.contact.name, zone=zone.name,
                             clinic=clinic.name)
                return
                        
            cba = Contact.objects.create(name=name, location=zone)
            cba.types.add(const.get_cba_type())
            self.msg.connection.contact = cba
            self.msg.connection.save()
            self.respond("Thank you %(name)s! You have successfully "
                         "registered as a RemindMi Agent for zone %(zone)s of %(clinic)s."
                         "%(notify_text)s",
                         name=cba.name, zone=zone.name , clinic=clinic.name,
                         notify_text=self._get_notify_text())
        else:
            self.respond("Sorry, I didn't understand that. Make sure you send "
                         "your clinic, zone #, and name like: AGENT <CLINIC "
                         "CODE> <ZONE #> <YOUR NAME>")

def get_unique_value(query_set, field_name, value, sep="_"):
    """Gets a unique name for an object corresponding to a particular
       django query.  Useful if you've defined your field as unique
       but are system-generating the values.  Starts by checking
       <value> and then goes to <value>_2, <value>_3, ... until 
       it finds the first unique entry. Assumes <value> is a string"""
    
    original_value = value
    column_count = query_set.filter(**{field_name: value}).count()
    to_append = 2
    while column_count != 0:
        value = "%s%s%s" % (original_value, sep, to_append)
        column_count = query_set.filter(**{field_name: value}).count()
        to_append = to_append + 1
    return value
