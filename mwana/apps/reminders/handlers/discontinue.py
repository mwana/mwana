import logging

from django.core.exceptions import ObjectDoesNotExist

from mwana import const
from rapidsms.models import Contact
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.router import send

# from mwana.malawi.lib import py_cupom


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
        # and get location details
        if self.msg.contact is not None:
            location = self.msg.contact.location.id
        else:
            self.respond(UNREGISTERED)
            return True

        text = text.strip()
        labels = ['m_first', 'm_last', 'dob']
        data = text.split()
        tokens = dict(zip(labels, data))
        # get contact of type Patient with matching name and dob
        # and is a patient
        try:
            patient = Contact.objects.location(location).get(
                first_name=tokens['m_first'],
                last_name=tokens['m_last'],
                types=const.get_patient_type())
        except:
            patient = None
            msg = "Sorry, we cannot find a patient with those details."
            send(msg, self.msg.connections[0])

        if patient is not None:
            if patient.is_active is False:
                msg = "This patient has already been discontinued. "
            else:
                msg = ""
            patient.is_active = False
            patient.save()
            msg += "You will no longer receive reminders for {first} {last}."\
                   " Thank you.".format(
                       first=tokens['m_first'],
                       last=tokens['m_last'])
            send(msg, self.msg.connections[0])
