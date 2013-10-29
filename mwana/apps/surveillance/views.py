# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import timedelta

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.locations.models import Location
from mwana.apps.reports.utils.htmlhelper import get_incident_report_html_dropdown
from mwana.apps.reports.utils.htmlhelper import get_month_end
from mwana.apps.reports.utils.htmlhelper import get_month_start
from mwana.apps.reports.utils.htmlhelper import read_date_or_default
from mwana.apps.reports.views import read_request
from mwana.apps.surveillance.models import Incident
from mwana.apps.surveillance.models import Report
from mwana.const import MWANA_ZAMBIA_START_DATE


class Expando:
    pass


def get_month_range_bounds(enddate1, monthrange, startdate1):
    end_date = min(max(enddate1, startdate1, MWANA_ZAMBIA_START_DATE), date.today())
    start_date = end_date - timedelta(days=30 * monthrange)
    start_date = get_month_start(start_date)
    end_date = get_month_end(end_date)
    return end_date, start_date


def get_location_type_display(code):
    if code == "cl":
        return 'Facility Birth'
    elif code == "hm":
        return 'Community Birth'
    return "Location not given"




def get_report_parameters(request):
    today = date.today()

    startdate1 = read_date_or_default(request, 'start_date', today - timedelta(days=1))
    enddate1 = read_date_or_default(request, 'end_date', today)
    monthrange = read_request(request, 'monthrange')
    if monthrange:
        monthrange = int(monthrange)
    else:
        monthrange = 12
    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")
    return enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange

def surveillance(request):
    today = date.today()

    startdate1 = read_date_or_default(request, 'startdate', today - timedelta(days=30))
    enddate1 = read_date_or_default(request, 'enddate', today)
    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, MWANA_ZAMBIA_START_DATE), date.today())

    districts = [str(loc.slug) for loc in Location.objects.filter(type__slug='districts', location__supportedlocation__supported=True).distinct()]
    provinces = [str(loc.slug) for loc in Location.objects.filter(type__slug='provinces', location__location__supportedlocation__supported=True).distinct()]
    cases = Incident.objects.all().exclude(report=None)
    selected_id = Report.objects.filter(value__gte=6).order_by('-date', '-value').values_list('incident')[0][0]
    reports = Report.objects.filter(date__gte=start_date, date__lte=end_date)

    return render_to_response('surveillance/surveillance.html',
                              {
                              "fstart_date": start_date.strftime("%Y-%m-%d"),
                              "fend_date": end_date.strftime("%Y-%m-%d"),
                              "cases5": get_incident_report_html_dropdown('cases5', cases, ""),
                              "cases1": get_incident_report_html_dropdown('cases1', cases, selected_id, False),
                              "cases2": get_incident_report_html_dropdown('cases2', cases, ""),
                              "cases3": get_incident_report_html_dropdown('cases3', cases, ""),
                              "cases4": get_incident_report_html_dropdown('cases4', cases, ""),
                              "districts": districts,
                              "provinces": provinces,
                              "reports": reports,
                              }, context_instance=RequestContext(request)
                              )