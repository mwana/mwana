import datetime
from django.db.models import Q
from mwana.apps.labresults.models import Payload
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers import KeywordHandler


class PayloadsHandler(KeywordHandler):
    """
    A simple app, that allows help admins to view via SMS payloads recieved.
    Usage:
    PAYLOAD <HOW-MANY-DAYS-AGO1> [<HOW-MANY-DAYS-AGO2>]
    The startdate and enddate are constructed from the two params depending on
    which param is greater.
    """

    keyword = "payloads|payload|paylod|paylods|paylaod|paylaods|palod|palods|\
paload|paloads"

    HELP_TEXT = "To view payloads, send <PAYLOADS> <FROM-HOW-MANY-DAYS-AGO> \
[<TO-HOW-MANY-DAYS-AGO>], e.g PAYLOAD 7 1, (between 7 days ago and 1 day ago)"
    UNGREGISTERED = "Sorry, you must be registered as HELP ADMIN to view \
payloads. If you think this message is a mistake, respond with keyword 'HELP'"

    def help(self):
        """ Default help handler """
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        # make sure they are registered with the system
        if not (self.msg.contact and self.msg.contact.is_help_admin):
            self.respond(self.UNGREGISTERED)
            return

        text = text.strip()
        if not text:
            self.help()
            return
        start_days_ago = end_days_ago = 0
        ic = InputCleaner()
        try:
            txt_start_days_ago = text.split()[0]
            start_days_ago = int(ic.words_to_digits(txt_start_days_ago))
        except (IndexError, ValueError, AttributeError, TypeError):
            start_days_ago = 0
        try:
            txt_end_days_ago = text.split()[1]
            end_days_ago = int(ic.words_to_digits(txt_end_days_ago))
        except (IndexError, ValueError, AttributeError, TypeError):
            end_days_ago = 0
        if start_days_ago < end_days_ago:
            start_days_ago, end_days_ago = end_days_ago, start_days_ago

        now = datetime.date.today()
        today = datetime.datetime(now.year, now.month, now.day)
        
        startdate = today - datetime.timedelta(days=start_days_ago)
        enddate = today - datetime.timedelta(days=end_days_ago - 1) - \
                    datetime.timedelta(seconds=0.1)

#        Not sure if uncommenting the code below will improve performance.
#        payloads = Payload.objects.filter(Q(incoming_date__gt=startdate) |
#                                          Q(incoming_date=startdate),
#                                          Q(incoming_date__lt=enddate) |
#                                          Q(incoming_date=enddate))

#        if not payloads:
#            self.respond("Period %(startdate)s to %(enddate)s. No payloads",
#                         startdate=startdate.strftime("%d/%m/%Y"),
#                         enddate=enddate.strftime("%d/%m/%Y"))
#            return

        from django.db import connection
        cursor = connection.cursor()

        cursor.execute('select source, count(*) as count from \
             labresults_payload where incoming_date BETWEEN %s AND %s group by \
             source', [startdate, enddate])
        rows = cursor.fetchall()
        if not rows:
            self.respond("Period %(startdate)s to %(enddate)s. No payloads",
                         startdate=startdate.strftime("%d/%m/%Y"),
                         enddate=enddate.strftime("%d/%m/%Y"))
            return

        #build formartted message
        msg_header = 'PAYLOADS. Period: %s to %s. ' % (startdate.strftime("%d/%m/%Y")
                                                       , enddate.strftime("%d/%m/%Y"))
        msg_data = ' ****'.join(row[0] + ";" + str(row[1]) for row in rows)
        full_msg = msg_header + msg_data

        self.respond(full_msg)




        