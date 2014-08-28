# vim: ai ts=4 sts=4 et sw=4

from rapidsms.models import Connection
from rapidsms.models import Backend
from rapidsms.models import Contact
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.backendtests.models import ForwardedMessage

class ForwardHandler(KeywordHandler):
    """
    A quick simple app, for testing an smpp backend
    """

    keyword = "forwardsms|forward sms|fowardsms|foward sms|fowardsms|foward sms"

    HELP_TEXT = "To forward a message send forwardsms <backend> message"
    UNGREGISTERED = "Sorry, you must be registered as HELP ADMIN to do that. \
If you think this message is a mistake, respond with keyword 'HELP'"

    def help(self):
        """ Default help handler """
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        # make sure they are registered with the system
        if not (self.msg.contact and self.msg.contact.is_help_admin):
            self.respond(self.UNGREGISTERED)
            return True

        my_text = text
        my_text = my_text.strip()

        if not my_text:
            self.help()
            return True

        parts = my_text.split()
        if len(parts) < 4:
            self.help()
            return True

        backend_id = my_text.split()[0].strip()

        msg = my_text.replace(backend_id, "").strip()

        if backend_id != 'zain-smpp':
            self.respond("You cannot forward on %s backend" % backend_id)
            return True

        contacts = Contact.active.filter(connection__identity__startswith='+26097', types__slug='worker')
#        contacts = Contact.active.filter(connection__identity__startswith='+260979565992', types__slug='worker')

        backend= Backend.objects.get(name=backend_id)

        for contact in contacts:
            identity = contact.default_connection.identity
            try:
                connection= Connection.objects.get_or_create(backend=backend,identity=identity)[0]

                ForwardedMessage.objects.create(connection=connection)
                OutgoingMessage(connection, msg).send()
            except:
                pass