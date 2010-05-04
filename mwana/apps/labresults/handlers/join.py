#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
from mwana import const
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.util import get_clinic_or_default

class JoinHandler(KeywordHandler):
    """
    """

    keyword = "j0in|join|jin|john|jo1n|jion|j01n|jon"

    PATTERN = re.compile(r"^(\w+)(\s+)(.{4,})(\s+)(\d+)$")
    
    PIN_LENGTH = 4     
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 1

    HELP_TEXT = "To register, send JOIN <CLINIC CODE> <NAME> <SECURITY CODE>"
    ALREADY_REGISTERED = "Your phone is already registered to %(name)s at %(location)s. To change name or clinic first reply with keyword 'LEAVE' and try again."
        
    def help(self):
        self.respond(self.HELP_TEXT)

    def mulformed_msg_help(self):
        self.respond("Sorry, I didn't understand that. "
                     "Make sure you send your location, name and pin "
                     "like: JOIN <CLINIC CODE> <NAME> <SECURITY CODE>.")

    def invalid_pin(self, pin):
        self.respond("Sorry, %s wasn't a valid security code. "
                     "Please make sure your code is a %s-digit number like %s. "
                     "Send JOIN <CLINIC CODE> <YOUR NAME> <SECURITY CODE>." % (pin,
                     self.PIN_LENGTH, ''.join(str(i) for i in range(1, int(self.PIN_LENGTH) + 1))))

    def handle(self, text):
        b = InputCleaner()
        if is_eligible_for_results(self.msg.connection):
            # refuse re-registration if they're still active and eligible
            self.respond(self.ALREADY_REGISTERED, 
                         name=self.msg.connection.contact.name,
                         location=self.msg.connection.contact.location)
            return
        
        text = text.strip()
        text = b.remove_double_spaces(text)
        if len(text) < (self.PIN_LENGTH + self.MIN_CLINIC_CODE_LENGTH + self.MIN_NAME_LENGTH + 3):
            self.mulformed_msg_help()
            return

        #signed pin
        if text[-5:-4] == '-' or text[-5:-4] == '+':
            self.invalid_pin(text[-5:])
            return
        #too long pin
        if ' ' in text and text[1 + text.rindex(' '):].isdigit() and len(text[1 + text.rindex(' '):]) > self.PIN_LENGTH:
            self.invalid_pin(text[1 + text.rindex(' '):])
            return
        #non-white space before pin
        if text[-5:-4] != ' ':
            self.respond("Sorry, you should put a space before your pin. "
                         "Please make sure your code is a %s-digit number like %s. "
                         "Send JOIN <CLINIC CODE> <YOUR NAME> <SECURITY CODE>." % (
                         self.PIN_LENGTH, ''.join(str(i) for i in range(1, int(self.PIN_LENGTH) + 1))))
            return
        #reject invalid pin
        user_pin = text[-4:]
        if not user_pin:
            self.help()
            return
        elif len(user_pin) < 4:
            self.invalid_pin(user_pin)
            return
        elif not user_pin.isdigit():
            self.invalid_pin(user_pin)
            return

        
        group = self.PATTERN.search(text)
        if group is None:
            self.mulformed_msg_help()
            return

        tokens = group.groups()
        if not tokens:
            self.mulformed_msg_help()
            return

        clinic_code = tokens[0].strip()
        clinic_code = b.try_replace_oil_with_011(clinic_code)
        name = tokens[2]
        name = name.title().strip()
        pin = tokens[4].strip()
        if len(pin) != self.PIN_LENGTH:
            self.respond(self.INVALID_PIN)
            return
        if not name:
            self.respond("Sorry, you must provide a name to register. %s" % self.HELP_TEXT)
            return
        try:
            location = Location.objects.get(slug__iexact=clinic_code)
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
                    location = clinic
            else:
                contact = Contact(location=location)
                clinic = location
            contact.name = name
            contact.pin = pin
            contact.save()
            contact.types.add(const.get_clinic_worker_type())
            
            self.msg.connection.contact = contact
            self.msg.connection.save()
            
            self.respond("Hi %(name)s, thanks for registering for DBS "
                         "results from Results160 as staff of %(location)s. "
                         "Your PIN is %(pin)s. "
                         "Reply with keyword 'HELP' if your information is not "
                         "correct.", name=contact.name, location=clinic.name,
                         pin =pin)
        except Location.DoesNotExist:
            self.respond("Sorry, I don't know about a location with code %(code)s. Please check your code and try again.",
                         code=clinic_code)

        