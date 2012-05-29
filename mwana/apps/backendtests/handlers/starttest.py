# vim: ai ts=4 sts=4 et sw=4

from rapidsms.models import Connection
from rapidsms.models import Backend
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
import logging

logger = logging.getLogger(__name__)

class ForwardHandler(KeywordHandler):
    """
    A simple app, that allows help admins to get the code for a facility
    """

    keyword = "stattest|stat test|starttest|start test|"

    HELP_TEXT = "I am sorry, I can't help you."
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

        if not text:
            self.help()
            return True

        count = 20
        try:
            count = int(text)
        except Exception, e:
            logger.warn(e)

        connection,_ = Connection.objects.get_or_create(identity='7160',
        backend=Backend.objects.get(name='mtn'))
        
        for i in range(count):
            OutgoingMessage(connection, 'acceptsms hello world').send()
        
        return True

        