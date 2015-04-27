# vim: ai ts=4 sts=4 et sw=4
import datetime
from datetime import timedelta
from django.shortcuts import render_to_response
from django.views.decorators.http import require_GET
from django.template import RequestContext
from django import forms

from django_tables2_reports.config import RequestConfigReport as RequestConfig


from mwana.apps.remindmi.views import FilteredSingleTableView
from .filters import MonitorSampleFilter, ResultsDeliveryFilter
from mwana.apps.monitor.tables import MonitorSampleTable, ResultsDeliveryTable
from mwana.apps.monitor.models import MonitorSample
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.tlcprinters.models import MessageConfirmation
from mwana import const


def get_results_delivery_data():
    end_date = datetime.date.today() + timedelta(days=1)
    start_date = end_date - timedelta(30)
    locations = Location.objects.filter(send_live_results=True)
    results = Result.objects.filter(verified=True,
                                    processed_on__gt=start_date,
                                    processed_on__lt=end_date)
    messages_confirmed = MessageConfirmation.objects.filter(
        confirmed=True,
        sent_at__gte=start_date,
        sent_at__lte=end_date)
    delivery_stats = []
    for location in locations:
        res = results.filter(clinic=location)
        new = res.filter(notification_status='new')
        notified = res.filter(notification_status='notified')
        sent = res.filter(notification_status='sent')
        hist_new = new.count()
        hist_notified = notified.count()
        hist_sent = sent.count()
        today_new = new.filter(arrival_date=datetime.date.today()).count()
        today_sent = sent.filter(
            result_sent_date=datetime.date.today()).count()
        num_lims = res.count()
        num_rsms = res.count()
        num_sent_out = sent.count()
        sent_printer = sent.filter(
            recipient__contact__types=const.get_dbs_printer_type()).count()
        sent_worker = sent.filter(
            recipient__contact__types=const.get_clinic_worker_type()).count()
        # receipt_confirmed = sent.filter(receipt_confirmed=True).count()
        printer_confirmed = messages_confirmed.filter(
            connection__contact__location=location).count()
        delivery_stats.append({'name': location.name, 'hmis': location.slug,
                               'district': location.parent.name,
                               'all_new': hist_new,
                               'all_notified': hist_notified,
                               'all_sent': hist_sent,
                               'new_today': today_new,
                               'sent_today': today_sent,
                               'num_lims': num_lims,
                               'num_rsms': num_rsms,
                               'num_sent_out': num_sent_out,
                               'sent_printer': sent_printer,
                               'sent_worker': sent_worker,
                               'receipt_confirmed': printer_confirmed})
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


class ResultsDeliveryList(FilteredSingleTableView):
    table_class = ResultsDeliveryTable
    template_name = 'monitor/sample_delivery_filtered.html'
    filter_class = ResultsDeliveryFilter
    queryset = get_results_delivery_data()


@require_GET
def result_delivery_stats(request):
    stats = get_results_delivery_data()
    f = ResultsDeliveryFilter(request.GET, queryset=stats)
    # form = ResultsDeliveryForm()
    table = ResultsDeliveryTable(stats)
    RequestConfig(request,
                  paginate={"per_page": 25, "page": 1}).configure(table)
    return render_to_response("monitor/sample_delivery.html",
                              {"table": table, "filter": f},
                              context_instance=RequestContext(request))
