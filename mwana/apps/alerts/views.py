# vim: ai ts=4 sts=4 et sw=4
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_GET
from mwana.apps.alerts.labresultsalerts.alerter import Alerter
from mwana.apps.reports.views import get_facilities_dropdown_html
from mwana.apps.reports.views import get_groups_dropdown_html
from mwana.apps.reports.views import read_request

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
    tracing_days = get_from_request(request, 'input_tracing_days')

    is_report_admin = False
    try:
        user_group_name = request.user.groupusermapping_set.all()[0].group.name
        if request.user.groupusermapping_set.all()[0].group.id in (1,2)\
        and ("moh" in user_group_name.lower() or "support" in user_group_name.lower()):
            is_report_admin = True
    except:
        pass

    rpt_group = read_request(request, "rpt_group")
    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")


    alerter = Alerter(request.user,rpt_group,rpt_provinces,rpt_districts)

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

    tracing_days, not_using_trace = alerter.get_clinics_not_using_trace_alerts(tracing_days)
    inactive_workers_alerts = alerter.get_inactive_workers_alerts()

    
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

                              'not_using_trace':not_using_trace,
                              'tracing_days':tracing_days,

                              'inactive_workers_alerts':inactive_workers_alerts,

                              'days':range(1, 60),
                              'is_report_admin': is_report_admin,
                              'region_selectable': True,
                              'rpt_group': get_groups_dropdown_html('rpt_group',rpt_group),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", alerter.get_rpt_provinces(request.user), rpt_provinces) ,
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", alerter.get_rpt_districts(request.user), rpt_districts) ,
                              }, context_instance=RequestContext(request)
                              )
