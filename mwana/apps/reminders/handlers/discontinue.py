from datetime import date, timedelta
import logging

from django.core.exceptions import ObjectDoesNotExist
from django import forms

from rapidsms.models import Contact, Connection, Backend
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.router import send

from mwana.apps.reminders import models as reminders
# from mwana.malawi.lib import py_cupom
from mwana import const


logger = logging.getLogger(__name__)

DISCONTINUE_HELP = """To stop receiving reminders send:
DISCONTINUE <MOTHERS_FIRST_NAME> <MOTHERS_SURNAME> <DOB>"""
UNREGISTERED = "Please register as an HSA before cancelling reminders."\
               " Send JOIN for help on how to join."
GARBLED_MSG = "Sorry, I don't understand: %s. Please send DISCONTINUE"\
              "to check the format."


class DiscontinueHandler(KeywordHandler):

    keyword = 'discontinue'

    def help(self):
        """Respond with the DISCONTINUE help message."""
        self.respond(DISCONTINUE_HELP)

    def handle(self, text):
        """ Cancel reminders for a patient"""
        # check validity of reporter

        # get location details
        if self.msg.contact is not None:
            location = self.msg.contact.location.id

        text = text.strip()
        labels = ['m_first', 'm_last', 'dob']
        data = text.split()
        tokens = dict(zip(labels, data))
        # get contact of type Patient with matching name and dob
        patient = Contact.objects.location(location).get(
            first_name=tokens['m_first'], last_name=tokens['m_last'])
        if patient is not None:
            patient.is_active = False
            patient.save()
            msg = "Thank you. You will no longer receive reminders for {first} {last} born {dob}.".format(first=tokens['m_first'],
                       last=tokens['m_last'],
                       dob=tokens['dob'])
            send(msg, self.msg.connections[0])
        else:
            msg = "Sorry, we cannot find a patient with those details."
            send(msg, self.msg.connections[0])
