# vim: ai ts=4 sts=4 et sw=4
"""
Import Incident Reports (cases) from DHO broadcast messages
"""
from mwana.apps.surveillance.models import MissingIncident
from mwana.apps.locations.models import Location
from decimal import Decimal
from django.db.utils import DatabaseError
from mwana.apps.surveillance.models import Source
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from mwana.apps.surveillance.models import Report
from mwana.apps.surveillance.models import Separator
from mwana.apps.surveillance.models import ImportedReport
from mwana.apps.broadcast.models import BroadcastMessage
from django.core.management.base import LabelCommand
from mwana.apps.surveillance.models import Incident
from rapidsms.contrib.messagelog.models import Message

from datetime import timedelta
import re
import logging

logger = logging.getLogger(__name__)
class Command(LabelCommand):
    help = ("Import Incident reports (cases) from DHO broadcast messages")

    def handle(self, * args, ** options):       
        self.import_cases()

    def import_cases(self):
        b = InputCleaner()
        loc=Location.objects.get(slug='403012')

        Separator.objects.get_or_create(text=',')
        Separator.objects.get_or_create(text='\.')
        Separator.objects.get_or_create(text=':')
        Separator.objects.get_or_create(text='and')
        Separator.objects.filter(text='.').delete()

        count = 0

        bms_1 = BroadcastMessage.objects.filter(importedreport=None, group='DHO', text__iregex='\d\s*,')
        bms_2 = BroadcastMessage.objects.filter(importedreport__report=None, group='DHO', text__iregex='\d\s*,')
        bms = bms_1 | bms_2
        for bm in bms:
            separators = [sep.text for sep in Separator.objects.all()] or [',']
            sep = str("|".join(separators))
            

            # @type bm BroadcastMessage
            tokens = re.split(sep, b.strip_non_or_bad_ascii(re.sub(r"\s+", " ", bm.text)))
            cases = tokens
            source = Source.objects.create(parsed=0)
            now = bm.date + timedelta(hours=2) #change from utc
            start_date = now - timedelta(seconds=5)
            msgs =  Message.objects.filter(direction='I', text__endswith=bm.text, contact=bm.contact, date__gt=start_date, date__lt=now )
            
            if msgs:
                source.message =  msgs[0]
                source.save()
            num = 0.0
            for case_rpt in cases:
                case_values = re.split("[\s|=|-|:]", case_rpt)
                if len(case_values) < 2 or not case_values[-1].isdigit():
                    try:
                        ImportedReport.objects.create(source_message=bm, unparsed=case_values)
                    except DatabaseError, e:
                        print e                    
                    continue
                num += 1
                incident_text = " ".join(case_values[:-1]).strip()
                incident = None
                
                if Incident.objects.filter(alias__name__iexact=incident_text):
                    incident = Incident.objects.get(alias__name__iexact=incident_text)
                else:
                    MissingIncident.objects.get_or_create(alias_text=incident_text)
                if not incident:
                    continue
                report = Report()
                report.incident = incident
                report.date = bm.date.date()               
                report.raw_value = case_rpt
                report.reporter = bm.contact

                value = 0
                value_text = case_values[-1]
                temp1 = b.try_replace_oil_with_011(value_text)
                if temp1.isdigit():
                    value = int(temp1)
                else:
                    value = b.words_to_digits(value_text) or 0

                report.value = value if value < 200 else 0
                report.source =  source
                try:
                    report.save()
                    ImportedReport.objects.create(source_message=bm, report=report)
                    count = count + 1
                except DatabaseError, e:
                    print e
                except ValueError, e:
                    report.location=loc
                    report.save()
                    print e

            if num > 0.0:
                source.parsed = Decimal(str((num/len(cases))))
                try:
                    source.save()
                except DatabaseError, e:
                    print e
            else:
                source.delete()
        print ("Added %s case reports."% (count))

    def __del__(self):
        pass
