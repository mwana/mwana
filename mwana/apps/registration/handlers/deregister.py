import logging
from mwana import const
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
logger = logging.getLogger(__name__)

class DeregisterHandler(KeywordHandler):


    keyword = "deregister|de-register|remove|deregistre|diregister|remove|diregistre|deregster|de-registre"


    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 2
    MIN_PHONE_LENGTH = 9

    HELP_TEXT = "To deregister a CBA, send DEREGISTER <CBA_PHONE_NUMBER> or send DEREGISTER <CBA_NAME>"
    INELIGIBLE = "Sorry, you are NOT allowed to deregister anyone. If you think this message is a mistake reply with keyword HELP"
    UNGREGISTERED = "Sorry, you must be registered with Results160 to receive DBS \
results. If you think this message is a mistake, respond with keyword 'HELP'"

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
        location = self.msg.contact.location
        if location.type == const.get_zone_type():
            location = location.parent
        cba = None

        if text[1:].isdigit() and len(text) >= self.MIN_PHONE_LENGTH:
            try:
                cba = \
                Contact.active.get(connection__identity__icontains=text,
                                   location__parent=location,
                                   types=const.get_cba_type())
            except Contact.DoesNotExist:
                self.respond('The phone number %(phone)s does not belong to any'
                             + ' CBA at %(clinic)s. Make sure you typed it '
                             + 'correctly', phone=text, clinic=location)
            except Contact.MultipleObjectsReturned:
                logger.warning("Bug. phone number %s is used by multiple cba's "
                +"at same clinic" % text)
                return

        if not cba:
            cbas = \
            Contact.active.filter(name__icontains=text,
                                  location__parent=location,
                                  types=const.get_cba_type())
            if not cbas:
                self.respond('The name %(name)s does not belong to any'
                             + ' CBA at %(clinic)s. Make sure you typed it '
                             + 'correctly', name=text,
                             clinic=location)
                return
            if len(cbas) == 1:
                cba = cbas[0]
            elif len(cbas) < 5:
                self.respond("Try sending DEREGISTER <CBA_PHONE_NUMBER>. Which "
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
            worker = self.msg.contact
            for help_admin in Contact.active.filter(is_help_admin=True):
                OutgoingMessage(
                                help_admin.default_connection,
                                "%s:%s has deregistered %s:%s of zone %s at %s" %
                                (worker.name,
                                worker.default_connection.identity,
                                cba.name,
                                cba.default_connection.identity,
                                cba.location.name,
                                location.name
                                )).send()
