import re
from mwana import const
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location
from rapidsms.models import Contact
from mwana.apps.labresults.util import is_already_valid_connection_type
from mwana.util import get_clinic_or_default, get_worker_type, get_location_type, LocationCode

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
        self.respond("Sorry, %s wasn't a valid security code. %s" % (pin, self.INVALID_PIN))

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
        new_pattern = re.compile(r"^(clinic|dho|hub|pho)(\s+)(\w+)(\s+)(.{1,})(\s+)(\d+)$", re.IGNORECASE)
        if new_pattern.findall(text) or text.strip().split()[0].lower() in \
        ('clinic','dho','hub','pho'):
            self.include_type = True
            self.PATTERN = new_pattern            
            self.INVALID_PIN = "Please make sure your code is a 4-digit number like 1234. Send JOIN <TYPE> <LOCATION CODE> <YOUR NAME> <SECURITY CODE>."

    def handle(self, text):

        tokens = self.check_message_valid_and_clean(text)
        
        if not tokens:
            return
        if self.include_type:
            slug = tokens[2]
            name = tokens[4].title().strip()
            pin = tokens[6]
            worker_type = get_worker_type(tokens[0])
            location_type = get_location_type(tokens[0])
        else:
            clinic_code = LocationCode(tokens[0])
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
            
            self.respond("Hi %(name)s, thanks for registering for "
                         "Results160 from %(location)s. "
                         "Your PIN is %(pin)s. "
                         "Reply with keyword 'HELP' if this is "
                         "incorrect", name=contact.name, location=clinic.name,
                         pin=pin)
        except Location.DoesNotExist:
            self.respond("Sorry, I don't know about a location with code %(code)s. Please check your code and try again.",
                         code=slug)

        