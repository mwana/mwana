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

_ = lambda s: s

UNREGISTERED = "Sorry, you must be registered to add new stock. Reply with HELP if you need assistance."

class NewStockHandler(KeywordHandler):
    """
    """

    keyword = "New Stock|new|new stok|NewStock|new stoc"

    HELP_TEXT = _("To add new stock, send NEW STOCK <drug-code1> <quantity1>, <drug-code2> <quantity2> e.g NEW STOCK DG99 100, DG80 15")
    
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
        tokens = set(my_text.split(delimeter))

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
            location = self.msg.contact.location
            c = ConfirmationCode.objects.create()
            trans = Transaction.objects.create(reference=c)
            trans.date =  datetime.datetime.now().date()
            trans.type = "d_f"
            trans.sms_user = self.msg.contact
            trans.valid = True

            for drug in tokens:
                 stock = Stock.objects.get(code=drug.split()[0])
                 acc = StockAccount.objects.get(location=location,stock=stock)
                 acc.amount += int(drug.split()[1])
                 stk = StockTransaction.objects.create(transaction=trans,amount=int(drug.split()[1]), stock=stock)
                 stk.save()
                 acc.save()
        
            trans.account_to =acc
            trans.status = "c"
            trans.save()
            drugs=""
            for drug in StockAccount.objects.filter(location=location):
                 drugs += drug.stock.code +" "+str(drug.amount)+" "

            self.respond("Thank you. Your new levels for the added drugs are as follows: " +drugs)





        

        

