import re
from mwana import const
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location, LocationType
from rapidsms.models import Contact
from mwana.apps.labresults.util import is_already_valid_connection_type
from mwana.apps.reminders import models as reminders
from mwana.util import get_clinic_or_default, get_worker_type, get_location_type, LocationCode
_ = lambda s: s

class JoinHandler(KeywordHandler):
    """
    """
    include_type = False
    keyword = "j0in|join|jin|john|jo1n|jion|j01n|jon"
    PIN_LENGTH = 4
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 2

    PATTERN = re.compile(r"^(\w+)(\s+)(.{1,})(\s+)(\d+)$")
    HELP_TEXT = "To register, send JOIN <TYPE> <LOCATION CODE> <NAME> <SECURITY CODE>"
    MALFORMED_MSG_TXT = "Sorry, I didn't understand that. Make sure you send your type, location, name and pin like: JOIN <TYPE> <LOCATION CODE> <NAME> <SECURITY CODE>."
    INVALID_PIN = "Please make sure your code is a 4-digit number like 1234. Send JOIN <LOCATION CODE> <YOUR NAME> <SECURITY CODE>."

    ALREADY_REGISTERED = "Your phone is already registered to %(name)s at %(location)s. To change name or location first reply with keyword 'LEAVE' and try again."
        
    def help(self):
        self.respond(self.HELP_TEXT)

    def mulformed_msg_help(self):
        self.respond(self.MALFORMED_MSG_TXT)

    def invalid_pin(self, pin):
        self.respond("Sorry, %s wasn't a valid pin code. %s" % (pin, self.INVALID_PIN))

    def check_message_valid_and_clean(self, text):
        '''
        Checks the message for general validity (correct pin length, number of keywords, etc) and
        returns False if message is somehow invalid (after firing off a useful response message)
        
        Returns cleaned message in tokenized format (tuple)
        '''
       
        cleaner = InputCleaner()
   
        text = text.strip()
        text = cleaner.remove_double_spaces(text)
        self.set_pattern_to_use(text)
        if len(text) < (self.PIN_LENGTH + self.MIN_CLINIC_CODE_LENGTH + self.MIN_NAME_LENGTH + 1):
            self.mulformed_msg_help()
            return False

        #signed pin
        if text[-5:-4] == '-' or text[-5:-4] == '+':
            self.invalid_pin(text[-5:])
            return False
        #too long pin
        if ' ' in text and text[1 + text.rindex(' '):].isdigit() and len(text[1 + text.rindex(' '):]) > self.PIN_LENGTH:
            self.invalid_pin(text[1 + text.rindex(' '):])
            return False
        #non-white space before pin
        if text[-5:-4] != ' ' and text[-4:-3] != ' ':
            self.respond("Sorry, you should put a space before your pin. %s" %
                         self.INVALID_PIN)
            return False
        #reject invalid pin
        user_pin = text[-4:]
        if not user_pin:
            self.help()
            return False
        elif len(user_pin) < 4:
            self.invalid_pin(user_pin)
            return False
        elif not user_pin.isdigit():
            self.invalid_pin(user_pin)
            return False

        group = self.PATTERN.search(text)
        if group is None:
            self.mulformed_msg_help()
            return False

        tokens = group.groups()
        if not tokens:
            self.mulformed_msg_help()
            return False
        #sanitize!
            
        group = self.PATTERN.search(text)

        tokens = group.groups()
        tokens = list(tokens)


        if self.include_type:
            type = tokens[0].strip() # type
            location_code = tokens[2].strip() #location code
            name = tokens[4].title().strip() #name
            pin = tokens[6].strip() #pin
        else:
            location_code = tokens[0].strip() #location code
            name = tokens[2].title().strip() #name
            pin = tokens[4].strip() #pin
        
        
        #more error checking
        if len(pin) != self.PIN_LENGTH:
            self.invalid_pin(pin)
            return False
        if not name:
            self.respond("Sorry, you must provide a name to register. %s" % self.HELP_TEXT)
            return False
        elif len(name) < self.MIN_NAME_LENGTH:
            self.respond("Sorry, you must provide a valid name to register. %s" % self.HELP_TEXT)
            return False
        
        return tuple(tokens)

    def set_pattern_to_use(self, text):
        new_pattern = re.compile(r"^(clinic|agent|dho|hub|pho)(\s+)(\w+)(\s+)(.{1,})(\s+)(\d+)$", re.IGNORECASE)
        if new_pattern.findall(text) or text.strip().split()[0].lower() in \
        ('clinic','dho','hub','pho'):
            self.include_type = True
            self.PATTERN = new_pattern            
            self.INVALID_PIN = "Please make sure your code is a 4-digit number like 1234. Send JOIN <TYPE> <LOCATION CODE> <YOUR NAME> <SECURITY CODE>."


    def get_response_message(self, worker_type, name, location, pin):
        response = ("Hi %(name)s, thanks for registering for Results160 from"
                         " %(location)s. Your PIN is %(pin)s. " 
                         "Reply with keyword 'HELP' if this is " 
                         "incorrect" % {'name':name, 'location':location, 'pin':pin})
        if worker_type == const.get_hub_worker_type():
            response = response.replace("for Results160 from", "for Results160 from hub at")
        elif worker_type == const.get_district_worker_type():
            response = response.replace(". Your PIN is ", " DHO. Your PIN is ")
        elif worker_type == const.get_province_worker_type():
            response = response.replace(". Your PIN is ", " PHO. Your PIN is ")        
        return response

    def handle(self, text):
        text = text.strip()
        cba_pattern = re.compile(r"^(cba|agent)(\s+)(\w+)(\s+)(.{1,})(\s+)$", re.IGNORECASE)
        if cba_pattern.findall(text) or text.strip().split()[0].lower() in \
        ('agent','cba'):
            self.handle_zone(text[text.index(' '):])
            return       

        tokens = self.check_message_valid_and_clean(text)
        
        if not tokens:
            return
        if self.include_type:
            slug = LocationCode(tokens[2]).slug
            name = tokens[4].title().strip()
            pin = tokens[6]
            worker_type = get_worker_type(tokens[0])
            location_type = get_location_type(tokens[0])
        else:
            slug = tokens[0]
            clinic_code = LocationCode(slug)
            name = tokens[2].title().strip()
            pin = tokens[4]
            worker_type = clinic_code.get_worker_type()
            location_type = clinic_code.get_location_type()
            slug = clinic_code.slug
        
        if is_already_valid_connection_type(self.msg.connection, worker_type):
            # refuse re-registration if they're still active and eligible
            self.respond(self.ALREADY_REGISTERED, 
                         name=self.msg.connection.contact.name,
                         location=self.msg.connection.contact.location)
            return False        
        try:
            location = Location.objects.get(slug__iexact=slug,
                                            type__slug__in=location_type)
            if self.msg.connection.contact is not None \
               and self.msg.connection.contact.is_active:
                # this means they were already registered and active, but not yet 
                # receiving results.
                clinic = get_clinic_or_default(self.msg.connection.contact) 
                if clinic != location:
                    self.respond(self.ALREADY_REGISTERED,
                                 name=self.msg.connection.contact.name,
                                 location=clinic)
                    return True
                else: 
                    contact = self.msg.contact
            else:
                contact = Contact(location=location)
                clinic = get_clinic_or_default(contact)
            contact.name = name
            contact.pin = pin            
            contact.save()
            contact.types.add(worker_type)
            
            self.msg.connection.contact = contact
            self.msg.connection.save()
            
            self.respond(self.get_response_message(worker_type, name, clinic.name, pin))
        except Location.DoesNotExist:
            self.respond("Sorry, I don't know about a location with code %(code)s. Please check your code and try again.",
                         code=slug)
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
        
    def handle_zone(self, text):
        PATTERN = re.compile(r"^\s*(?:clinic\s+)?(?P<clinic>\S+)\s+(?:zone\s+)?(?P<zone>\S+)\s+(?:name\s+)?(?P<name>.+)$")
        HELP_TEXT = _("To register as a RemindMi agent, send JOIN <CBA> <CLINIC CODE> "\
                "<ZONE #> <YOUR NAME>")

        m = PATTERN.search(text)
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
            msg.append(HELP_TEXT)

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

    
