from mwana.util import get_clinic_or_default
from mwana.util import get_contact_type_slug
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Contact
from mwana.apps.smgl import const


class QuitHandler(KeywordHandler):
    keyword = "quit"

    def help(self):
        return self.handle("")

    def handle(self, text):

        msg = self.msg

        connection = msg.connection

        if not connection.contact:
            return self.respond(const.NOT_REGISTERED_FOR_DATA_ASSOC % {'name': connection.contact.name})

        if connection.contact.has_quit == True:
        	return self.respond("You have already quit mUbumi.")

        connection.contact.is_active = False
        connection.contact.has_quit = True
        connection.contact.save()
        return self.respond(const.QUIT_COMPLETE % {'name': connection.contact.name})

