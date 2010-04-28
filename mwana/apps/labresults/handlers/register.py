#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
from mwana import const
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact

class RegisterHandler(KeywordHandler):
    """
    """

    keyword = "join|j0in|jo1n|j01n"

    PATTERN = re.compile(r"^(\w+)(\s+)(.{4,})(\s+)(\d+)$")
    HELP_TEXT = "To register, send JOIN <CLINIC CODE> <NAME> <SECURITY CODE>"
    PIN_LENGTH = 4     
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 1

    
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
        #refuse re-registration
        if self.msg.contact is not None:
            self.respond("I already have a contact with phone %(identity)s.", identity=self.msg.connection.identity)
            return

        text = text.strip()
        text = b.remove_double_spaces(text)
        if len(text) < (self.PIN_LENGTH + self.MIN_CLINIC_CODE_LENGTH + self.MIN_NAME_LENGTH + 3):
            self.mulformed_msg_help()
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
            contact = Contact.objects.create(name=name, location=location, pin=pin, 
                                             is_results_receiver=True)
            contact.types.add(const.get_clinic_worker_type())
            self.msg.connection.contact = contact
            self.msg.connection.save()
            self.respond("Hi %(name)s, thanks for registering for DBS "
                         "results from Results160 as staff of %(location)s. "
                         "Reply with keyword 'HELP' if your information is not "
                         "correct.", name=contact.name, location=location.name)
        except Location.DoesNotExist:
            self.respond("Sorry, I don't know about a location with code %(code)s. Please check your code and try again.",
                         code=clinic_code)

        