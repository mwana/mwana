import re

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location, LocationType
from rapidsms.models import Contact

from mwana.apps.reminders import models as reminders
from mwana import const

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

class AgentHelper(KeywordHandler):
    """
    """

    keyword = "agent|agemt|urgent|ajent|agdmt|agnt|agant"

    PATTERN = re.compile(r"^\s*(?:clinic\s+)?(?P<clinic>\S+)\s+(?:zone\s+)?(?P<zone>\S+)\s+(?:name\s+)?(?P<name>.+)$")
    HELP_TEXT = _("To register as a RemindMi agent, send AGENT <CLINIC CODE> "\
                "<ZONE #> <YOUR NAME>")
    
    def help(self):
        self.respond(self.HELP_TEXT)

    def _get_notify_text(self):
        events = reminders.Event.objects.values_list('name', flat=True)
        events = [event_name.lower() for event_name in events]
        if len(events) == 2:
            events = (' ' + _('or') + ' ').join(events)
        elif len(events) > 0:
            if len(events) > 2:
                events[-1] = _('or') + ' ' + events[-1]
            events = ', '.join(events)
        if events:
            return _("Please notify us next time there is a %(event)s in your "
                     "zone."), {'event': events}
        else:
            return "", {}

    def _get_or_create_zone(self, clinic, name):
        # create the zone if it doesn't already exist
        zone_type, _ = LocationType.objects.get_or_create(slug=const.ZONE_SLUGS[0])
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

    def _get_clinic_and_zone(self, contact):
        """
        Determines the contact's current clinic and zone, if any.
        """
        if contact and contact.location and\
           contact.location.type.slug in const.ZONE_SLUGS:
            contact_clinic = contact.location.parent
            contact_zone = contact.location
        elif contact and contact.location and\
             contact.location.type.slug in const.CLINIC_SLUGS:
            contact_clinic = contact.location
            contact_zone = None
        else:
            contact_clinic = None
            contact_zone = None
        return contact_clinic, contact_zone

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
                self.respond(_("Sorry, I don't know about a clinic with code "
                             "%(code)s. Please check your code and try again."),
                             code=clinic_slug)
                return
            zone = self._get_or_create_zone(clinic, zone_slug)
            contact_clinic, contact_zone =\
              self._get_clinic_and_zone(self.msg.contact)
            
            if contact_zone == zone:
                # don't let agents register twice for the same zone
                self.respond(_("Hello %(name)s! You are already registered as "
                             "a RemindMi Agent for zone %(zone)s of %(clinic)s."), 
                             name=self.msg.contact.name, zone=zone.name,
                             clinic=clinic.name)
                return
            elif contact_clinic and contact_clinic != clinic:
                # force agents to leave if they appear to be switching clinics
                self.respond(_("Hello %(name)s! You are already registered as "
                             "a RemindMi Agent for %(old_clinic)s. To leave "
                             "your current clinic and join %(new_clinic)s, "
                             "reply with LEAVE and then re-send your message."),
                             name=self.msg.contact.name,
                             old_clinic=contact_clinic.name,
                             new_clinic=clinic.name)
                return
            elif self.msg.contact:
                # if the contact exists but wasn't registered at a location,
                # or was registered at the clinic level instead of the zone
                # level, update the record and save it
                cba = self.msg.contact
                cba.name = name
                cba.location = zone
                cba.save()
            else:
                # lastly, if no contact exists, create one and save it in the
                # connection
                cba = Contact.objects.create(name=name, location=zone)
                self.msg.connection.contact = cba
                self.msg.connection.save()
            if not cba.types.filter(slug=const.CLINIC_WORKER_SLUG).count():
                cba.types.add(const.get_cba_type())
            msg = self.respond(_("Thank you %(name)s! You have successfully "
                                 "registered as a RemindMi Agent for zone "
                                 "%(zone)s of %(clinic)s."), name=cba.name,
                                 zone=zone.name, clinic=clinic.name)
            notify_text, kwargs = self._get_notify_text()
            if notify_text:
                msg.append(notify_text, **kwargs)
        else:
            msg = self.respond(_("Sorry, I didn't understand that."))
            msg.append(self.HELP_TEXT)

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
