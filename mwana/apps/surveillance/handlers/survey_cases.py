# vim: ai ts=4 sts=4 et sw=4
from decimal import Decimal
from mwana.apps.surveillance.models import Source
from datetime import datetime
from mwana.apps.surveillance.models import Report
from mwana.apps.surveillance.models import Incident
import re
from datetime import date
from datetime import timedelta
from rapidsms.contrib.messagelog.models import Message

from mwana.apps.surveillance.models import Separator
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from datetime import timedelta
from mwana.apps.stringcleaning.inputcleaner import strip_non_or_bad_ascii
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class SurveyCaseHandler(KeywordHandler):
    """
    """

    keyword = "case|cases|survey|surveys|suvey|suveys|case.|cases.|survey.|surveys.|suvey.|suveys.|case,|cases,|survey,|surveys,|suvey,|suveys,|case;|cases;|survey;|surveys;|suvey;|suveys;"
 
    HELP_TEXT = "To report cases, send CASE <DATE or WEEK_OF_YEAR> <CASE-1> <VALUE-1>, <CASE-2> <VALUE-2>, e.g. CASE 17/10/2013, TB 12, D20 12. or Case 44, TB 12, D20 12"
    UNREGISTERED = "Sorry, you must be registered with Results160 before you can start reporting cases. Reply with HELP if you need assistance."

    def help(self):
        self.respond(self.HELP_TEXT)    
        
    def _parse_time(self, date_str):
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
        b = InputCleaner()
        if not self.msg.contact:
            self.respond(self.UNREGISTERED)
            return

        separators = [',', ';'] + [sep.text for sep in Separator.objects.all()] or [',']
        sep = "|".join(separators)
        
        tokens = re.split(sep, strip_non_or_bad_ascii(text))
        
        rpr_time = self._parse_time(tokens[0])

        if rpr_time and isinstance(rpr_time, int):
            given_date = Report.get_date(rpr_time)
            today = date.today()
            if given_date < today and (today - given_date).days > 30:
                self.respond("Sorry, make sure you use the correct week or year")
                return True
        
        cases = tokens
        if rpr_time:
            cases = tokens[1:]

        if not cases:
            self.help()
            return

        if cases[0].strip()[0].isdigit():
            self.help()
            return
        
        success = False
        source = Source.objects.create(parsed=0)
        now = datetime.now()
        start_date = now - timedelta(seconds=5)
        msgs =  Message.objects.filter(direction='I', text=self.msg.raw_text, contact=self.msg.contact, date__gt=start_date, date__lt=now )

        if msgs:
            source.message =  msgs[0]
            source.save()
        num = 0.0
        for case_rpt in cases:
            case_values = re.split("[\s|=|-|:]", case_rpt)
            if len(case_values) < 2 or not case_values[-1].isdigit():
                continue
            num += 1
            incident_text = " ".join(case_values[:-1]).strip()
            incident = None
            if Incident.objects.filter(alias__name__iexact=incident_text):
                incident = Incident.objects.get(alias__name__iexact=incident_text)
            else:
                incident = Incident.objects.create(name=incident_text)

            report = Report()
            report.incident = incident
            if rpr_time:
                if isinstance(rpr_time, date):
                    report.date = rpr_time
                elif isinstance(rpr_time, int):
                    report.week_of_year = rpr_time
            
                       
            report.source =  source
            report.raw_value = case_rpt

            report.reporter = self.msg.contact

            value = 0
            value_text = case_values[-1]
            temp1 = b.try_replace_oil_with_011(value_text)
            if temp1.isdigit():
                value = int(temp1)
            else:
                value = b.words_to_digits(value_text) or 0

            report.value = value
            report.save()
            success = True
        
        if success:
            source.parsed = Decimal(str((num/len(cases))))
            source.save()
            self.respond("Thank you %s for the report." % (self.msg.contact))
        else:
            source.delete()
            self.help()
        
        return True

            
            
        
            
        
        