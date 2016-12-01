# vim: ai ts=4 sts=4 et sw=4
import datetime
import re

from mwana.apps.stockmini.models import StockOnHand

from mwana.apps.stockmini.models import Stock
from mwana.apps.stock.models import Transaction
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from dateutil.parser import parse

_ = lambda s: s

UNREGISTERED = "Sorry, you must be registered to report stock levels. Reply with HELP if you need assistance."


class StockHandler(KeywordHandler):
    """
    """

    keyword = "stock|stalk|stork|stok|stoke|st0ck|st0rk|st0k|st0ke"

    HELP_TEXT = _("To report stock levels, send Stock <date> <code> <level>"
                  "The date is optional and is logged as TODAY if left out.")

    message_to_lender = "Hi %s, %s has confirmed receipt of the drugs you loaned them"

    def help(self):
        self.respond(self.HELP_TEXT)

    def _is_valid_date_string(self, date_text):
        try:
            if "/" not in date_text:
                return False
            parse(date_text)
            return True
        except ValueError:
            return False

    def handle(self, text):
        if not self.msg.contact:
            self.respond(UNREGISTERED)
            return True

        my_text = text.strip().upper()

        if " " not in my_text:
            self.help()
            return True

        my_text = re.sub(r"\s+", " ", my_text)
        if my_text != " ":
            this_text = my_text.split()
            string_date = this_text[0]
            if not self._is_valid_date_string(string_date):
                self.respond("Please enter a valid date. The expected format is mm/dd/YYYY")
                return True
            date_part = string_date.split('/')
            date = datetime.date(int(date_part[2]), int(date_part[1]), int(date_part[0]))
            today = datetime.date.today()
            three_months_ago = today - datetime.timedelta(days=90)
            if date > today:
                self.respond("Sorry you can't enter a date after today's date. "
                             "%s is a future date." % date.strftime('%d/%b/%Y'))
                return True
            elif date < three_months_ago:
                self.respond("Sorry you can't enter a date more than three months ago. "
                             "%s is too far in the past" % date.strftime('%d/%b/%Y'))
                return True
            s = Stock.objects.get(code=this_text[1].strip())
            level = this_text[2]
            try:
                level = abs(int(
                    level))  # we do not want negative values for stock levels so we change negative values to positive.
            except ValueError:
                self.respond("Please enter a valid integer for the stock level")
                return True

            location = self.msg.contact.location

            if StockOnHand.objects.filter(date=date, stock=s, facility=location):
                stock_on_hand = StockOnHand.objects.get(date=date, stock=s, facility=location)
                stock_on_hand.level = level
                stock_on_hand.save()
            else:
                stock_on_hand = StockOnHand.objects.create(date=date, stock=s, level=level, facility=location)

            self.respond(
                "Thank you for reporting the stock level as {0:d} for {1:s} on {2:s}. "
                "If you think this message is a mistake"
                " reply with HELP.".format(stock_on_hand.level,
                                           stock_on_hand.stock.name, stock_on_hand.date.strftime('%d/%b/%Y')))
            return True
