# vim: ai ts=4 sts=4 et sw=4
import re

from mwana.apps.stock.models import ConfirmationCode
from mwana.apps.stock.models import Stock
from mwana.apps.stock.models import StockAccount
from mwana.apps.stock.models import StockTransaction
from mwana.apps.stock.models import Transaction
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.db.models import Q

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
        
        valid_drug_ids = list(set([id[0].upper() for id in Stock.objects.values_list('code').distinct()] + [id[0].upper() for id in Stock.objects.values_list('short_code').distinct()]))
        
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

            return True

        else:
            location = self.msg.contact.location
            confirmation_code = ConfirmationCode.objects.create()
            trans = Transaction.objects.create(reference=confirmation_code)
            trans.type = "d_f"
            trans.sms_user = self.msg.contact
            trans.valid = True

            user_drug_codes = []
            for drug in tokens:
                 drug_code = drug.split()[0]
                 delimeter = '-'
                 for c in '_#$%@=/+:':
                    drug_code = drug_code.replace(c, delimeter)

                 user_drug_codes.append(drug_code.upper())
                 stock = Stock.objects.get(Q(code__iexact=drug_code)|Q(short_code__iexact=drug_code))
                 acc, created = StockAccount.objects.get_or_create(location=location,stock=stock)
                 acc.amount += int(drug.split()[1])
                 stk = StockTransaction.objects.create(transaction=trans, 
                                                        amount=int(drug.split()[1]),
                                                        stock=stock)
                 stk.save()
                 acc.save()
        
            trans.account_to = acc
            trans.status = "c"
            trans.save()
            
            updated_drugs = list(set(StockAccount.objects.filter(location=location, stock__code__in=user_drug_codes) | StockAccount.objects.filter(location=location, stock__short_code__in=user_drug_codes)))
            last_part = ", ".join(str(drug.amount) + " units of " + drug.stock.code for drug in updated_drugs)

            self.respond("Thank you. New levels for the added stock are: %s. Cc: %s" % (last_part, confirmation_code))
