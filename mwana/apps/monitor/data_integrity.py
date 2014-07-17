# vim: ai ts=4 sts=4 et sw=4


from mwana.apps.labresults.models import Result
from django.db.models import F


class Expando():
    pass


def dbs_collection_date_after_entered_on():
    """
    -ve transport time
    """
    return Result.objects.filter(collected_on__gt=F('entered_on'))


def dbs_entered_on_after_processed_on():
    """
    -ve processing time
    """
    return Result.objects.filter(entered_on__gt=F('processed_on'))


def dbs_processed_on_after_arrival_date():
    """
    -ve delay time (data entry time + transmission time)
    """
    return Result.objects.filter(processed_on__gt=F('arrival_date'))


def dbs_arrival_date_after_result_sent_date():
    """
    -ve retrieving time
    """
    return Result.objects.filter(arrival_date__gt=F('result_sent_date'))


def dbs_with_date_issues():
    """
    -ve retrieving time
    """
    return Result.objects.filter(collected_on__gt=F('entered_on')) | \
           Result.objects.filter(entered_on__gt=F('processed_on')) | \
           Result.objects.filter(processed_on__gt=F('arrival_date')) | \
           Result.objects.filter(arrival_date__gt=F('result_sent_date'))


#def get_dbs_with_transport_issues():
#    list1 = []
#    for res in dbs_collection_date_after_entered_on().\
#    filter(result_sent_date=None).distinct():
#        obj = Expando()
#        obj.lab = res.payload.source.title()
#        obj.id = res.sample_id
#        obj.issue = 'Collection date incorrect'
#        list1.append(obj)
#
#    list2 = []
#    for res in dbs_entered_on_after_processed_on().\
#    filter(result_sent_date=None).distinct():
#        obj = Expando()
#        obj.lab = res.payload.source.title()
#        obj.id = res.sample_id
#        obj.issue = 'Test date incorrect'
#        list2.append(obj)
#
#    list2 = []
#    for res in dbs_entered_on_after_processed_on().\
#    filter(result_sent_date=None).distinct():
#        obj = Expando()
#        obj.lab = res.payload.source.title()
#        obj.id = res.sample_id
#        obj.issue = 'Test date incorrect'
#        list2.append(obj)
#
#
#    return sorted(list1, key=lambda x: x.lab)


