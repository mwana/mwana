# vim: ai ts=4 sts=4 et sw=4
import datetime
import re

from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.reminders import models as reminders
from mwana.apps.stock.models import ConfirmationCode
from mwana.apps.stock.models import Stock
from mwana.apps.stock.models import StockAccount
from mwana.apps.stock.models import StockTransaction
from mwana.apps.stock.models import Transaction
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from mwana.apps.broadcast.models import BroadcastMessage
from rapidsms.messages.outgoing import OutgoingMessage

_ = lambda s: s

UNREGISTERED = "Sorry, you must be registered to confirm. Reply with HELP if you need assistance."

class ConfirmHandler(KeywordHandler):
    """
    """

    keyword = "trans|Received|recieved|receved|recived|riviece"

    HELP_TEXT = _("To confirm a transaction, send Received <code> e.g Received 15122")
    message_to_lender = "Hi %s, %s has confirmed receipt of the drugs you loaned them"
    
    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond(UNREGISTERED)
            return True

        confirmation_code = text.strip().upper()

        trans = Transaction.objects.get(reference=confirmation_code)
        trans_type = trans.type
        if (trans.status == 'p'):
            if(trans_type == "f_f"):
                acc_to = trans.account_to
                acc_from = trans.account_from
                lending_staff=trans.sms_user
                if((acc_to.pending_amount > 0) and (acc_from.pending_amount > 0)):
                    acc_to.amount+=acc_to.pending_amount
                    acc_from.amount-=acc_from.pending_amount
                    acc_to.pending_amount=0
                    acc_from.pending_amount=0
                    clinic_to=acc_to.location
                    trans.status = "c"
                    acc_to.save()
                    acc_from.save()
                    trans.save()

                    self.respond("Thank you for confirming that you have received the drugs")
                    self.broadcast(self.message_to_lender, lending_staff, clinic_to,"CLINIC")

        else:
            self.respond("A completed transaction cannot be confirm. Kindly ensure you have sent the correct confirmation code")
                

    def broadcast(self, text, contact, clinic_to, group_name):

        message_body = "%(text)s"

#        for contact in contacts:
#            if contact.default_connection is None:
#                self.info("Can't send to %s as they have no connections" % contact)
#            else:
        OutgoingMessage(contact.default_connection, message_body,
                                **{"text": (text % (contact.name, clinic_to))}).send()

        logger_msg = getattr(self.msg, "logger_msg", None)
        if not logger_msg:
            self.error("No logger message found for %s. Do you have the message log app running?" %\
                       self.msg)
        bmsg = BroadcastMessage.objects.create(logger_message=logger_msg,
                                               contact=self.msg.contact,
                                               text=text,
                                               group=group_name)
        bmsg.recipients = contacts
        bmsg.save()
        return True



            




        

        

