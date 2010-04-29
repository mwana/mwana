from datetime import datetime, timedelta
import rapidsms
from mwana.apps.broadcast.models import BroadcastMessage, BroadcastResponse
from rapidsms.messages.outgoing import OutgoingMessage

NO_CONTACT = "Sorry %(sender)s, but we don't have any information about %(recipient)s anymore so we were unable to send your response"
class App (rapidsms.App):
    
    BLAST_RESPONSE_WINDOW_HOURS = 4
    
    def default(self, message):
        # In the default phase, after everyone has had a chance to deal
        # with this message, check if it might be a response to a previous
        # blast, and if so pass along to the original sender
        if message.contact:
            window = datetime.utcnow() - timedelta(hours=self.BLAST_RESPONSE_WINDOW_HOURS)
            broadcasts = BroadcastMessage.objects.filter\
                (date__gte=window, recipients=message.contact)
            if broadcasts.count() > 0:
                latest_broadcast = broadcasts.order_by("-date")[0]
                if not latest_broadcast.contact.default_connection:
                    self.info("Can't send to %s as they have no connections" % \
                              latest_broadcast.contact)
                    message.respond(NO_CONTACT, sender=message.contact.name, 
                                    recipient=latest_broadcast.contact)
                else: 
                    response = OutgoingMessage(latest_broadcast.contact.default_connection, 
                                               "%(text)s [from %(user)s]",
                                               **{"text": message.text, "user": message.contact.name})
                    response.send()
                    
                    logger_msg = getattr(response, "logger_msg", None) 
                    if not logger_msg:
                        self.error("No logger message found for %s. Do you have the message log app running?" %\
                                   self.msg)
                    BroadcastResponse.objects.create(broadcast=latest_broadcast,
                                                     contact=message.contact,
                                                     text=message.text,
                                                     logger_message=logger_msg)
                return True
