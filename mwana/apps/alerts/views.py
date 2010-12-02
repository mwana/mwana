# vim: ai ts=4 sts=4 et sw=4
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_GET
from mwana.apps.alerts.labresultsalerts.alerter import Alerter

def get_int(val):
    return int(val) if str(val).isdigit() else None

def get_from_request(request, name):
    try:
        return get_int(request.REQUEST[name])
    except KeyError:
        return None


@require_GET
def mwana_alerts (request):
    transport_time = get_from_request(request, 'input_transport_time')
    retrieving_time = get_from_request(request, 'input_retrieving_time')
    notifying_time = get_from_request(request, 'input_notifying_time')
    lab_processing_days = get_from_request(request, 'input_lab_processing_days')
    lab_sending_days = get_from_request(request, 'input_lab_sending_days')


    alerter = Alerter()
    transport_time, not_sending_dbs_alerts = \
        alerter.get_districts_not_sending_dbs_alerts(transport_time)
    retrieving_time, not_retrieving_results = \
        alerter.get_clinics_not_retriving_results_alerts(retrieving_time)
    notifying_time, not_notifying_or_using_results = \
        alerter.get_clinics_not_sending_dbs_alerts(notifying_time)

    lab_processing_days, not_processing_dbs = \
        alerter.get_labs_not_processing_dbs_alerts(lab_processing_days)

    lab_sending_days, not_sending_dbs = \
        alerter.get_labs_not_sending_payloads_alerts(lab_sending_days)

    return render_to_response('alerts/alerts.html',
                              {
                              'not_sending_dbs_alerts':not_sending_dbs_alerts,
                              'transport_time':transport_time,

                              'not_retrieving_results':not_retrieving_results,
                              'retrieving_time':retrieving_time,

                              'not_notifying_or_using_results':not_notifying_or_using_results,
                              'notifying_time':notifying_time,

                              'not_processing_dbs':not_processing_dbs,
                              'lab_processing_days':lab_processing_days,

                              'not_sending_dbs':not_sending_dbs,
                              'lab_sending_days':lab_sending_days,

                              'days':range(1, 60),
                              }, context_instance=RequestContext(request)
                              )
