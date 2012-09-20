# vim: ai ts=4 sts=4 et sw=4
"""
This handler is suppose to be modified into a scheduled task.
"""
import re
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from mwana.apps.reminders.models import PatientEvent

import logging

from django.db import transaction
from django.conf import settings

from mwana import const
_ = lambda s: s


class BirthRecordHandler(KeywordHandler):
    """
    """

    keyword = "record|recod"

    PATTERN = re.compile(r"^(\w+)(\s+)(.{1,})(\s+)(\d+)$")

    PIN_LENGTH = 4
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 2

    HELP_TEXT = "To register, send JOIN <CLINIC CODE> <NAME> <PIN CODE>"
    ALREADY_REGISTERED = "Your phone is already registered to %(name)s at %(location)s. To change name or clinic first reply with keyword 'LEAVE' and try again."

    def help(self):
        self.respond(self.HELP_TEXT)

    def mulformed_msg_help(self):
        self.respond(_("Sorry, I didn't understand that. "
                     "Make sure you send your location, name and pin "
                     "like: JOIN <CLINIC CODE> <NAME> <PIN CODE>."))

    def get_locations_with_births(self):
        locs=[]
#        births = PatientEvent.objects.filter(event='birth')
        births = PatientEvent.objects.filter(notification_status='new')
        for birth in births:
            try:
                location= birth.cba_conn.contact.location.parent
                if location not in locs:
                    locs.append(location)
            except AttributeError:
                pass
        return locs


    def handle(self, text):
        locations = self.get_locations_with_births()
        for location in locations:
            birth = PatientEvent.objects.filter(cba_conn__contact__location__parent=location,notification_status='new')[0]
            contacts=Contact.active.filter(location=birth.cba_conn.contact.location.parent)
            for contact in contacts:
                self.respond("Hello %s. We have %s births for %s. Please send: birthreg <PIN> to retrieve them." % \
                             (contact.name, len(birth), contact.location.name))


