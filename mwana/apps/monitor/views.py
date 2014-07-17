# vim: ai ts=4 sts=4 et sw=4

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.monitor.data_integrity import dbs_collection_date_after_entered_on
from mwana.apps.monitor.data_integrity import dbs_entered_on_after_processed_on
from mwana.apps.monitor.data_integrity import dbs_processed_on_after_arrival_date


def data_integrity_issues(request):

    dbs_collection_date_issues = dbs_collection_date_after_entered_on().\
        filter(result_sent_date=None).exclude(notification_status='obsolete').\
        order_by('payload__source', 'id')

    dbs_test_date_issues = dbs_entered_on_after_processed_on().\
        filter(result_sent_date=None).exclude(notification_status='obsolete').\
        order_by('payload__source', 'id')
    
    dbs_arrival_date_issues = dbs_processed_on_after_arrival_date().\
        filter(result_sent_date=None).exclude(notification_status='obsolete').\
        order_by('payload__source', 'id')

    return render_to_response('monitor/data_integrity_issues.html',
                              {
                              'dbs_collection_date_issues': dbs_collection_date_issues,
                              'dbs_test_date_issues': dbs_test_date_issues,
                              'dbs_arrival_date_issues': dbs_arrival_date_issues,
                              }, context_instance=RequestContext(request)
                              )
