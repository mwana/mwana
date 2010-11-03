import re
from mwana import const
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location
from rapidsms.models import Contact
from mwana.apps.labresults.util import is_already_valid_connection_type
from mwana.util import get_clinic_or_default

class JoinHandler(KeywordHandler):
    """
    """

    keyword = "j0in|join|jin|john|jo1n|jion|j01n|jon"
    
    PATTERN = re.compile(r"^(\w+)(\s+)(.{1,})(\s+)(\d+)$")
    
    PIN_LENGTH = 4     
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 2

    HELP_TEXT = "To register, send JOIN <LOCATION CODE> <NAME> <SECURITY CODE>"
    ALREADY_REGISTERED = "Your phone is already registered to %(name)s at %(location)s. To change name or location first reply with keyword 'LEAVE' and try again."
        
    def help(self):
        self.respond(self.HELP_TEXT)

    def mulformed_msg_help(self):
        self.respond("Sorry, I didn't understand that. "
                     "Make sure you send your location, name and pin "
                     "like: JOIN <LOCATION CODE> <NAME> <SECURITY CODE>.")

    def invalid_pin(self, pin):
        self.respond("Sorry, %s wasn't a valid security code. "
                     "Please make sure your code is a %s-digit number like %s. "
                     "Send JOIN <LOCATION CODE> <YOUR NAME> <SECURITY CODE>." % (pin,
                     self.PIN_LENGTH, ''.join(str(i) for i in range(1, int(self.PIN_LENGTH) + 1))))


    def check_message_valid_and_clean(self, text):
        '''
        Checks the message for general validity (correct pin length, number of keywords, etc) and
        returns False if message is somehow invalid (after firing off a useful response message)
        
        Returns cleaned message in tokenized format (tuple)
        '''
        
        cleaner = InputCleaner()
        
        group = self.PATTERN.search(text)
        if group is None:
            self.mulformed_msg_help()
            return False

        tokens = group.groups()
        if not tokens:
            self.mulformed_msg_help()
            return False


        text = text.strip()
        text = cleaner.remove_double_spaces(text)
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
            self.respond("Sorry, you should put a space before your pin. "
                         "Please make sure your code is a %s-digit number like %s. "
                         "Send JOIN <LOCATION CODE> <YOUR NAME> <SECURITY CODE>." % (
                         self.PIN_LENGTH, ''.join(str(i) for i in range(1, int(self.PIN_LENGTH) + 1))))
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
        
        #sanitize!
            
        group = self.PATTERN.search(text)

        tokens = group.groups()
        tokens = list(tokens)
        tokens[0] = tokens[0].strip()[0:6] #location code
        tokens[2] = tokens[2].title().strip() #name
        tokens[4] = tokens[4].strip() #pin
        
        
        #more error checking
        if len(tokens[4]) != self.PIN_LENGTH:
            self.respond(self.INVALID_PIN)
            return False
        if not tokens[2]:
            self.respond("Sorry, you must provide a name to register. %s" % self.HELP_TEXT)
            return False
        elif len(tokens[2]) < self.MIN_NAME_LENGTH:
            self.respond("Sorry, you must provide a valid name to register. %s" % self.HELP_TEXT)
            return False
        
        if len(tokens[0]) == 4:
            tokens[0] = tokens[0] + '00' #pad with 00 for district code
        
        return tuple(tokens)


    def get_worker_type(self, code):
        '''
        Returns the worker_type based on the location_code
        Expects code of format PPDDFF exactly.
        '''
        PP = code[0:2]
        DD = code[2:4]
        FF = code[4:6]
        
        if FF == '00':
            if DD == '00':
                return const.get_province_worker_type()
            else:
                return const.get_district_worker_type()
        else:
            return const.get_clinic_worker_type()
        
    def get_location_type(self, code):
        '''
        Returns the location_type_slug (Province, district or clinic) based on the location_code
        Expects code of format PPDDFF exactly.
        '''
        PP = code[0:2]
        DD = code[2:4]
        FF = code[4:6]
        print 'WOOP WOOP!'
        if FF == '00':
            if DD == '00':
                return const.PROVINCE_SLUGS
            else:
                return const.DISTRICT_SLUGS
        else:
            return const.CLINIC_SLUGS  
        
    def handle(self, text):

        tokens = self.check_message_valid_and_clean(text)
        
        if not tokens:
            return

        clinic_code = tokens[0]
        name = tokens[2]
        pin = tokens[4]
        worker_type = self.get_worker_type(clinic_code)
        location_type = self.get_location_type(clinic_code)
        
        if is_already_valid_connection_type(self.msg.connection, worker_type):
            # refuse re-registration if they're still active and eligible
            self.respond(self.ALREADY_REGISTERED, 
                         name=self.msg.connection.contact.name,
                         location=self.msg.connection.contact.location)
            return False
        
        try:
            location = Location.objects.get(slug__iexact=clinic_code,
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
                         code=clinic_code)

        