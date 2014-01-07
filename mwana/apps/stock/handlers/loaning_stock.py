# vim: ai ts=4 sts=4 et sw=4
import datetime
import re

from mwana import const
from mwana.const import get_clinic_worker_type
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.reminders import models as reminders
from mwana.apps.stock.models import ConfirmationCode
from mwana.apps.stock.models import Stock
from mwana.apps.stock.models import StockAccount
from mwana.apps.stock.models import StockTransaction
from mwana.apps.stock.models import Transaction
from mwana.apps.stock.models import Threshold
from mwana.apps.broadcast.models import BroadcastMessage
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact

_ = lambda s: s

UNREGISTERED = "Sorry, you must be registered to add new stock. Reply with HELP if you need assistance."

class LoaningStockHandler(KeywordHandler):
    """
    """

    keyword = "LOAN|loan|lon"

    HELP_TEXT = _("To loan drugs, send LOAN <location code> <drug-code1> <quantity1>, <drug-code2> <quantity2> e.g LOAN 111111 DG99 100, DG80 15")
    message_to_clinic = "Hi %s, %s have loaned you the following drugs: %s. Confirm with code %s when you get the stock"
    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond(UNREGISTERED)
            return True

        my_text = text.strip().upper()

        if " " not in my_text:
            self.help()
            return True
        delimeter = ','
        for c in ';.:':
            my_text = my_text.replace(c, delimeter)

        my_text = re.sub(r"\s+", " ", my_text)
        this_text= my_text.split(delimeter)

        temp = str(this_text[0])
        temp = temp.split(" ")
        clinic_to = temp.pop(0)
        tokens = ' '.join(temp)
        tokens = set(tokens.split(","))

        drug_ids = [drug.split()[0] for drug in tokens]
        repeating_drugs = [id for id in drug_ids if drug_ids.count(id) > 1]


        if repeating_drugs:
            self.respond("Sorry, drug ID(s) %s appears more than once in your message" % ", ".join(set(repeating_drugs)))
            return True



        valid_drug_ids = [id[0].upper() for id in Stock.objects.values_list('code').distinct()]

        invalid_ids = list(set(drug_ids) - set(valid_drug_ids))

        if invalid_ids:
            if len(invalid_ids) == 1:
                self.respond("Sorry, I don't know stock with code %s. Please check your spelling and try again. If you think this message is a mistake send HELP." % invalid_ids[0])
            else:
                self.respond("Sorry, I don't know stock with codes %s. Please check your spelling and try again. If you think this message is a mistake send HELP." % ", ".join(invalid_ids))

            return True

        invalid_quantities = [drug.split()[1] for drug in tokens if not drug.split()[1].isdigit()]
        if invalid_quantities:
            if len(invalid_quantities) ==1:
                self.respond("Sorry, %s is not a valid number. Enter only numbers for quantity." % invalid_quantities[0])
            else:
                self.respond("Sorry, %s are not valid numbers. Enter only numbers for quantity." % ", ".join(invalid_quantities))

        else:
            location_from = self.msg.contact.location
            location_to = Location.objects.get(slug=clinic_to)            
            confirmation_code = ConfirmationCode.objects.create()
            print (location_to)
            print (confirmation_code)
            trans = Transaction.objects.create(reference=confirmation_code)
            trans.date =  datetime.datetime.now().date()
            trans.type = "f_f"
            trans.sms_user = self.msg.contact
            trans.valid = True
            drugs_below_threshold=""
            drugs=""

            for drug in tokens:
                 amount = int(drug.split()[1])
                 stock = Stock.objects.get(code=drug.split()[0])
                 acc_from = StockAccount.objects.get(location=location_from,stock=stock)
                 acc_from.pending_amount = amount #amount to be deducted when receiving clinic confirms.
                 acc_to = StockAccount.objects.get(location=location_to,stock=stock)
                 acc_to.pending_amount = amount #amount to be added when receiving clinic confirms receipt of drugs.
                 stk = StockTransaction.objects.create(transaction=trans,amount=amount, stock=stock)
                 stk.save()
                 acc_from.save()
                 acc_to.save()

                 print (acc_from)
                 threshold=Threshold.objects.get(account=acc_from)
                 drugs += stock.code +" "+str(abs(amount))+" "

                 if((acc_from.amount-acc_from.pending_amount) <= threshold.level):
                     drugs_below_threshold += stock.code +" "+str(abs(acc_from.amount))+" "

            trans.account_to =acc_to
            trans.account_from =acc_from
            trans.status = "p"
            trans.save()
            
            
            if (drugs_below_threshold):
                self.respond("You cannnot proceed with loan because your stock level will be below threshold for the following drugs: " +drugs_below_threshold)
            else:                                 
                self.respond("Thank you. You have loaned %s the following drugs: " +drugs +"" %location_to)
                staff = Contact.active.location(location_to)#.filter(types=get_clinic_worker_type())
                print (staff)
                self.broadcast(self.message_to_clinic, staff, "CLINIC", drugs, clinic_to, confirmation_code)


    def broadcast(self, text, contacts, group_name, drugs, clinic_to, confirmation_code):

        message_body = "%(text)s"

        for contact in contacts:
            if contact.default_connection is None:
                self.info("Can't send to %s as they have no connections" % contact)
            else:
                OutgoingMessage(contact.default_connection, message_body,
                                **{"text": (text % (contact.name, clinic_to, drugs, confirmation_code))}).send()

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









