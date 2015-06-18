# vim: ai ts=4 sts=4 et sw=4
import datetime
from datetime import timedelta
from django.shortcuts import render_to_response
from django.views.decorators.http import require_GET
from django.template import RequestContext
from django import forms
from django.conf import settings
from django.db.models import Q

from django_tables2_reports.config import RequestConfigReport as RequestConfig


from mwana.apps.remindmi.views import FilteredSingleTableView
from .filters import MonitorSampleFilter, ResultsDeliveryFilter
from mwana.apps.monitor.tables import MonitorSampleTable, ResultsDeliveryTable
from mwana.apps.monitor.models import MonitorSample
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.nutrition.views import get_report_criteria
# from mwana.apps.tlcprinters.models import MessageConfirmation
from mwana import const

DISTRICTS = settings.DISTRICTS


def percent(num=None, den=None):
    if num is None or num == 0:
        return int(0)
    elif den is None or den == 0:
        return int(0)
    else:
        return int(100 * num / float(den))


def get_results_delivery_data(location, startdate, enddate):
    end_date = enddate
    start_date = startdate
    location = location
    locations = Location.objects.filter(send_live_results=True)
    results = Result.objects.filter(verified=True,
                                    processed_on__gt=start_date,
                                    processed_on__lt=end_date)
    if location == "All Districts":
        pass
    else:
        results = results.filter(clinic__parent__name=location)
        locations = locations.filter(parent__name=location)
    delivery_stats = []
    for location in locations:
        res = results.filter(clinic=location)
        new = res.filter(notification_status='new')
        sent = res.filter(notification_status='sent')
        hist_new = new.count()
        num_lims = res.count()
        num_rsms = res.count()
        num_sent_out = sent.count()
        sent_printer = sent.filter(
            recipient__contact__types=const.get_dbs_printer_type()).count()
        sent_worker = sent.filter(
            recipient__contact__types=const.get_clinic_worker_type()).count()
        percentage_sent = percent(num_sent_out, num_lims)
        delivery_stats.append({'name': location.name, 'hmis': location.slug,
                               'district': location.parent.name,
                               'all_new': hist_new,
                               'num_lims': num_lims,
                               'num_rsms': num_rsms,
                               'num_sent_out': num_sent_out,
                               'sent_printer': sent_printer,
                               'sent_worker': sent_worker,
                               'percentage_sent': percentage_sent})
    return delivery_stats


class ResultsDeliveryForm(forms.Form):
    facility = forms.CharField(label='Facility Name', max_length=100,
                               required=False)
    hmis = forms.CharField(label='HMIS Code', max_length=100,
                           required=False)
    district = forms.CharField(label='District', max_length=100,
                               required=False)


class MonitorSampleList(FilteredSingleTableView):
    model = MonitorSample
    table_class = MonitorSampleTable
    template_name = 'monitor/monitor_sample_list.html'
    filter_class = MonitorSampleFilter
    queryset = MonitorSample.objects.all()


@require_GET
def result_delivery_stats(request):
    location, startdate, enddate = get_report_criteria(request)
    selected_location = str(location)
    stats = get_results_delivery_data(location, startdate, enddate)
    activity = request.GET.get("activity", 'all')
    selected_activity = activity
    if activity == 'active':
        stats = [i for i in stats if i['num_lims'] > 0]
    elif activity == 'inactive':
        stats = [i for i in stats if i['num_lims'] == 0]
    f = ResultsDeliveryFilter(request.GET, queryset=stats)
    form = ResultsDeliveryForm()
    table = ResultsDeliveryTable(stats)
    districts = DISTRICTS
    RequestConfig(request,
                  paginate={"per_page": 25, "page": 1}).configure(table)
    return render_to_response("monitor/sample_delivery.html",
                              {"table": table, "filter": f, 'form': form,
                               "startdate": startdate, "enddate": enddate,
                               "selected_location": selected_location,
                               "selected_activity": selected_activity,
                               "districts": districts},
                              context_instance=RequestContext(request))
