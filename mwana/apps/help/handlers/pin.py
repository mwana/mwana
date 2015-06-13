# vim: ai ts=4 sts=4 et sw=4
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from rapidsms.router import send


class PinHandler(KeywordHandler):
    """
    Allows help admins to retrieve PIN code for a user
    """

    keyword = "PIN"

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
            connection__identity__contains=phone_number)
        if not contacts:
            self.respond("There are no active SMS users with phone number "
                         "matching %s" % phone_number)
            return True

        msg_string = " ".join("%s: %s." % (contact.name, contact.pin) for \
                               contact in contacts[:4])

        # self.respond(msg_string)
        for contact in contacts:
            pin_code = contact.pin
            conn = [contact.default_connection]
            msg = "Your pin code is %s. Please do not forget this and delete this message after reading." % pin_code
            send(msg, conn)
        return True
