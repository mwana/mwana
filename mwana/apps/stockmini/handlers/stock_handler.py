# vim: ai ts=4 sts=4 et sw=4
import datetime
import re
from datetime import date
from mwana.apps.stockmini.models import StockOnHand
from mwana.apps.stockmini.models import Stock
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


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

    def _parse_date(self, date_str):
        if date_str.strip().isdigit():
            week_of_year = abs(int(date_str))
            if week_of_year > 53:
                return None
                # don't go back too far
                #            if week_of_year < int((date.today().strftime('%U'))) - 6:
                #                return None

            return week_of_year

        text = date_str.strip()
        text = re.sub(r"\s+", " ", text)
        tokens = re.split("[\s|\-|/|\.]", date_str.strip())
        tokens = [t for t in tokens if t]

        if len(tokens) != 3:
            return None

        values = [val.strip() for val in tokens if val.strip().isdigit()]

        if len(values) != 3:
            return None

        return date(int(values[2]), int(values[1]), int(values[0]))


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
            if not self._parse_date(string_date):
                self.respond("Please enter a valid date. You entered %s" % string_date)
                return True
            else:
                my_date = self._parse_date(string_date)
            today = datetime.date.today()
            three_months_ago = today - datetime.timedelta(days=90)
            if my_date > today:
                self.respond("Sorry you can't enter a date after today's date. "
                             "%s is a future date." % my_date.strftime('%d/%b/%Y'))
                return True
            elif my_date < three_months_ago:
                self.respond("Sorry you can't enter a date more than three months ago. "
                             "%s is too far in the past" % my_date.strftime('%d/%b/%Y'))
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

            if StockOnHand.objects.filter(date=my_date, stock=s, facility=location):
                stock_on_hand = StockOnHand.objects.get(date=my_date, stock=s, facility=location)
                stock_on_hand.level = level
                stock_on_hand.save()
            else:
                stock_on_hand = StockOnHand.objects.create(date=my_date, stock=s, level=level, facility=location)

            self.respond(
                "Thank you for reporting the stock level as {0:d} for {1:s} on {2:s}. "
                "If you think this message is a mistake"
                " reply with HELP.".format(stock_on_hand.level,
                                           stock_on_hand.stock.name, stock_on_hand.date.strftime('%d/%b/%Y')))
            return True
