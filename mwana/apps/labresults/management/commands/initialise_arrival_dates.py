"""
Sets labresults.Result.arrival_date to the the value the first payload with the
result arrived
"""

import json

from datetime import datetime
from django.core.management.base import LabelCommand
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.views import dictval

BU_START_DATE = datetime(2010, 7, 9)
UNICEF_START_DATE = datetime(2010, 6, 14)

class Command(LabelCommand):
    help = "Sets the arrival date to the the value the result first arrived."
    args = "<file_path>"
#    label = 'valid file path'
    
    def handle(self, * args, ** options):
        import_arrival_dates()
        import_arrival_dates()

    def __del__(self):
        pass


def import_arrival_dates():
    """
    
    """
    print ''
    count = 0
    success = True
    if Result.objects.filter(arrival_date=None).exclude(result=None).count() == 0:
        print "---" * 20
        print "\nDB table OK. All results already have arrival_dates"
        print "---" * 20
        input = raw_input("Do you still want to update (y/n)?\n")
        if not (input[:1] in "yY"):
            return
    for res in Result.objects.exclude(arrival_date=None):
        res.arrival_date = None
        res.save()

    for payload in Payload.objects.filter():
        print '.',
        data = json.loads(payload.raw)
        sample_id = None
        for record in data['samples']:
            sample_id = dictval(record, 'id')
            clinic_code = str(dictval(record, 'fac'))[:6]
            pat_id = str(dictval(record, 'pat_id'))

            if sample_id:
                try:
                    old_record = \
                    Result.objects.get(sample_id=sample_id,
                                       requisition_id=pat_id,
                                       clinic__slug__iexact=clinic_code)
                    # for BU skip payloads before pilot
                    if old_record.clinic.slug.startswith('80') and payload.incoming_date < BU_START_DATE:
                        continue
                    if old_record.clinic.slug.startswith('80'):
                        date_to_use = BU_START_DATE
                    else:
                        date_to_use =UNICEF_START_DATE
                    if old_record.arrival_date:
                        old_record.arrival_date = max(date_to_use, min(old_record.arrival_date,
                                                      payload.incoming_date))
                    else:
                        old_record.arrival_date = max(payload.incoming_date, date_to_use)
                    old_record.save()
                    count = count + 1
                except Result.DoesNotExist:
                    pass

    print "\nupdated %s results" % count

