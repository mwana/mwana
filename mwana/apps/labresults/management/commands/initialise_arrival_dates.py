"""
Sets labresults.Result.arrival_date to the the value the first payload with the
result arrived
"""

import json

from django.core.management.base import LabelCommand
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.views import dictval

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
        return True

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
                    if old_record.arrival_date:
                        old_record.arrival_date = min(old_record.arrival_date,
                                                      payload.incoming_date)
                    else:
                        old_record.arrival_date = payload.incoming_date
                    old_record.save()
                    count = count + 1
                except Result.DoesNotExist:
                    pass

    print "\nupdated %s results" % count
    
