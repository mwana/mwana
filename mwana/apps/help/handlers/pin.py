# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.help.models import HelpRequest
from mwana.util import get_clinic_or_default
from mwana.util import get_contact_type_slug
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Contact
_ = lambda s: s

RESPONSE           = _("Sorry you're having trouble%(person)s. Your help request has been forwarded to a support team member and they will call you soon.")
ANONYMOUS_FORWARD  = "Someone has requested help. Please call them at %(phone)s."
CONTACT_FORWARD    = "%(name)s has requested help. Please call them at %(phone)s."
CON_LOC_FORWARD    = "%(name)s at %(location)s has requested help. Please call them at %(phone)s."
ADDITIONAL_INFO    = "Their message was: %(message)s"

class PinHandler(KeywordHandler):
    """
    Allows help admins to retrieve PIN code for a user
    """

    keyword = "PIN|PIN."
        
    HELP_TEXT = "To get the PIN for a user, send PIN <PHONE_NUMBER_PATTERN>"
    UNGREGISTERED = "Sorry, you must be registered as HELP ADMIN to retrieve \
PIN codes. If you think this message is a mistake, respond with keyword 'HELP'"

    def help(self):
        """ Default help handler """
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        # make sure they are registered with the system
        if not (self.msg.contact and self.msg.contact.is_help_admin):
            self.respond(self.UNGREGISTERED)
            return

        text = text.strip()
        if not text:
            self.help()
            return

        phone_number = text.strip()
        contacts = Contact.active.filter(
                                         connection__identity__contains=\
                                         phone_number)
        if not contacts:
            self.respond("There are no active SMS users with phone number "
                         "matching %s" % phone_number)
            return True

        msg_string = " ".join("%s: %s." % (contact.name, contact.pin) for \
                               contact in contacts[:4])

        self.respond(msg_string)
        return True