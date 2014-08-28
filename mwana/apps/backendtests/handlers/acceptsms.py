# vim: ai ts=4 sts=4 et sw=4

from rapidsms.models import Contact
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage

class ForwardHandler(KeywordHandler):
    """
    A quick simple app, for testing an smpp backend
    """

    keyword = "acceptsms|accept sms|aceptsms|acept sms"

    HELP_TEXT = "I am sorry, I can't help you."
    UNGREGISTERED = "Sorry, you must be registered as HELP ADMIN to do that. \
If you think this message is a mistake, respond with keyword 'HELP'"

    def help(self):
        """ Default help handler """
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        
        if not ('0978775414' in self.msg.connection.identity):
            return True

        contacts = Contact.active.filter(connection__backend__name='zain-smpp', types__slug='worker', location__slug='999999')
        


        for contact in contacts:
            OutgoingMessage(contact.default_connection,
            "Thank you %s. Stress testing is finishing now. Sorry for the incovenince. Don't reply" % contact.name).send()

        return True