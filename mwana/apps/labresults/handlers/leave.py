from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

BYE_MSG   = _("You have successfully unregistered, %(name)s. We're sorry to see you go.")
ERROR_MSG = _("Whoops - you tried to unregister from the system but I don't know who you are! Don't worry, you won't be receiving any messages from us.")

class UnregisterHandler(KeywordHandler):
    """
    """

    keyword = "leave|unregister|unreg"
    
    def help(self):
        # Because we want to process this with just an empty keyword, rather
        # than respond with a help message, just call the handle method from
        # here.
        self.handle("")

    def handle(self, text):
        if self.msg.connection.contact:
            name = self.msg.connection.contact.name
            # we just deactivate the contact, but don't delete it, because 
            # there could be all kinds of useful foreign key goodies attached.
            self.msg.connection.contact.is_active = False
            self.msg.connection.contact.save()
            # we also disassociate the contact from the connection
            self.msg.connection.contact = None
            self.msg.connection.save()
            self.respond(BYE_MSG, name=name)
        else:
            self.respond(ERROR_MSG)
            