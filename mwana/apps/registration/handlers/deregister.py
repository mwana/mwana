import logging

from mwana import const
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
logger = logging.getLogger(__name__)

class DeregisterHandler(KeywordHandler):


    keyword = "deregister|de-register|remove|deregistre|diregister|rimove|diregistre|deregster|de-registre"


    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 2
    MIN_PHONE_LENGTH = 9

    HELP_TEXT = "To deregister a CBA, send REMOVE <CBA_PHONE_NUMBER> or send REMOVE <CBA_NAME>"
    INELIGIBLE = "Sorry, you are NOT allowed to deregister anyone. If you think this message is a mistake reply with keyword HELP"
    
    FOLLOWUP_MESSAGE = "Make a followup for a failed CBA deregistration due to a"\
" phone number %s being shared by multiple CBA's. Deregistration"\
" was attempted by %s:%s of %s"

    def help(self):
        self.respond(self.HELP_TEXT)


    def handle(self, text):
        b = InputCleaner()
        if not is_eligible_for_results(self.msg.connection):
            # essentially checking for an active clinic_worker
            self.respond(self.INELIGIBLE)
            return

        text = text.strip()
        text = b.remove_double_spaces(text)
        worker = self.msg.contact
        location = worker.location
        if location.type == const.get_zone_type():
            location = location.parent
        cba = None

        # we expect phone numbers like +260977123456, 0977123456, 977123456
        # (a phone number is unique to each cba at a clinic)
        if text[1:].isdigit() and len(text) >= self.MIN_PHONE_LENGTH:
            try:
                cba = \
                Contact.active.get(connection__identity__endswith=text,
                                   location__parent=location,
                                   types=const.get_cba_type())
            except Contact.DoesNotExist:
                self.respond('The phone number %(phone)s does not belong to any'
                             ' CBA at %(clinic)s. Make sure you typed it '
                             'correctly', phone=text, clinic=location)
            # we do not expect this to happen. phone number is excpected to be
            # unique (>=9 chars) project wide
            except Contact.MultipleObjectsReturned:
                logger.warning("Bug. phone number %s is used by multiple cba's "
                               "at same clinic" % text)

                self.respond("Sorry %(name)s, the CBA with phone number %(phone)s"
                             " could not be deregistered. This matter will be"
                             " followed up by Support Staff immediately",
                             name=worker.name, phone=text)

                msg = (self.FOLLOWUP_MESSAGE % (text, worker.name,
                       worker.default_connection.identity,
                       location.name))
                self.notify_help_admins(msg)
                return

        if not cba:
            cbas = \
            Contact.active.filter(name__icontains=text,
                                  location__parent=location,
                                  types=const.get_cba_type())
            if not cbas:
                self.respond('The name %(name)s does not belong to any'
                             ' CBA at %(clinic)s. Make sure you typed it '
                             'correctly', name=text,
                             clinic=location)
                return
            if len(cbas) == 1:
                cba = cbas[0]
            elif len(cbas) < 5:
                self.respond("Try sending REMOVE <CBA_PHONE_NUMBER>. Which "
                             + "CBA did you mean? %(cbas)s", cbas=' or '.join(
                             cba.name + ":" + cba.default_connection.identity
                             for cba in cbas))
                return
            else:
                self.respond("There are %(len)s CBA's who's names match %(name)s"
                             + " at %(clinic)s. Try to use the phone number "
                             + "instead", len=len(cbas), name=text,
                             clinic=location.name)
                return
        if cba:
            cba.is_active = False
            cba.save()
            self.respond("You have successfully deregistered %(name)s:"
                         + "%(phone)s of zone %(zone)s at %(clinic)s",
                         name=cba.name, phone=cba.default_connection.identity,
                         zone=cba.location.name, clinic=location.name)
            msg = ("%s:%s has deregistered %s:%s of zone %s at %s" %
                   (worker.name,
                   worker.default_connection.identity,
                   cba.name,
                   cba.default_connection.identity,
                   cba.location.name,
                   location.name))
            self.notify_help_admins(msg)

    def notify_help_admins(self, msg):
        for help_admin in Contact.active.filter(is_help_admin=True):
            OutgoingMessage(help_admin.default_connection, msg).send()