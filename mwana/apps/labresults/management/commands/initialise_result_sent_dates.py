"""
Sets labresults.Result.result_sent_date to the the value the result was sent for
results that were sent before this field was added. The dates are extracted from
message logs
"""

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from django.db.models import Q
from mwana.apps.labresults.models import Result
from rapidsms.contrib.messagelog.models import Message

class Command(LabelCommand):
    help = "Sets the sent date to the the value the result was sent."
    args = "<file_path>"
#    label = 'valid file path'
    
    def handle(self, * args, ** options):
        import_sent_dates()
                
    def __del__(self):
        pass

def get_msgs_with_live_results():
    return Message.objects.filter(
                                  Q(direction__iexact='O'),
                                  Q(text__icontains='**** ') &
                                  Q(text__icontains='ected')).exclude(
                                   Q(text__icontains='Sample 9999') |
                                   (Q(text__icontains='**** 9990') &
                                   Q(text__icontains='**** 9991') &
                                   Q(text__icontains='**** 9992')))

def get_results_from_display(key):
    dict = {
    'Detected':['P'],
    'NotDetected':['N'],
    'Rejected':['R', 'X', 'I'],
    'Indeterminate':['R', 'X', 'I'],
    }
    return dict[key]

def import_sent_dates():
    """
    If labresults.Result.result_sent_date is null update it by extracting from 
    message logs the date when the result was sent
    """
    print ''
    if Result.objects.filter(result_sent_date=None,
                             notification_status='sent').count() == 0:        
        print "\nAll sent results already have result_sent_dates"
        return
    
    messages = get_msgs_with_live_results()

    num_of_updates = 0
    for msg in messages:
        location = msg.connection.contact.location
        result_texts = msg.text.replace('**** ', '').\
            replace('Thank you! Here are your results:', '.').\
                replace(' ', '').split('.')
        if '' in result_texts:
            result_texts.remove('')

        possible_payloads = []
        for result_text in result_texts:
            req_id = result_text.split(';')[0]
            actual_results = get_results_from_display(result_text.split(';')[1])            
            try:
                result = Result.objects.get(clinic=location,
                                            requisition_id=req_id,
                                            result__in=actual_results,
                                            notification_status='sent')
                if result.result_sent_date is None:
                    result.result_sent_date = msg.date
                    result.save()
                    possible_payloads.append(result.payload)
                    num_of_updates = num_of_updates + 1
                    print '.',
            except Result.MultipleObjectsReturned:
                try:
                    result = Result.objects.get(clinic=location,
                                                requisition_id=req_id,
                                                result__in=actual_results,
                                                notification_status='sent',
                                                payload__in=possible_payloads,
                                                result_sent_date=None)
                    result.result_sent_date = msg.date
                    result.save()
                    num_of_updates = num_of_updates + 1
                    print '.',
                except Result.DoesNotExist:
#                    print possible_payload.id
                    try:
                        result = Result.objects.get(clinic=location,
                                                    requisition_id=req_id,
                                                    result__in=actual_results,
                                                    notification_status='sent',
                                                    result_sent_date=None)
                        result.result_sent_date = msg.date
                        result.save()
                        num_of_updates = num_of_updates + 1
                        print '.',
                    except (Result.DoesNotExist,Result.MultipleObjectsReturned):
    #                    print possible_payload.id
                        results = Result.objects.filter(clinic=location,
                                                    requisition_id=req_id,
                                                    result__in=actual_results,
                                                    notification_status='sent',
                                                    result_sent_date=None)
                        if not results:
                            continue
                        print "\nFailed to map %s results:" %len(results)
                        print "".join("SampleID:" +
                                                               r.sample_id +
                                                               ", Req_ID:" +
                                                               r.requisition_id
                                                               + ", Result: "
                                                               + r.result for r in results)
                        print '.',
                except Result.DoesNotExist:
                    print "\nCould not find result to match: %s:%s:%s; Req_ID:%s  Result:%s ; Sent on:%s" % \
                    (location.id,
                     location.slug, location.name,
                     req_id,
                     actual_results, msg.date)

    print '\nFinished updating %s records' % num_of_updates


