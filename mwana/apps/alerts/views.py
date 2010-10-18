
from django.views.decorators.http import require_GET
from mwana.apps.alerts.labresultsalerts.alerter import Alerter
from rapidsms.utils import render_to_response

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


    alerter = Alerter()
    transport_time, not_sending_dbs_alerts = \
    alerter.get_districts_not_sending_dbs_alerts(transport_time)
    retrieving_time, not_retrieving_results = alerter.get_clinics_not_retriving_results_alerts(retrieving_time)

    return render_to_response(request, 'alerts/alerts.html',
                              {
                              'not_sending_dbs_alerts':not_sending_dbs_alerts,
                              'not_retrieving_results':not_retrieving_results,
                              't_days':range(1, 60),
                              'r_days':range(1, 30),
                              'transport_time':transport_time,
                              'retrieving_time':retrieving_time,
                              })
