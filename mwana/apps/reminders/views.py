# vim: ai ts=4 sts=4 et sw=4
import csv

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic.list import ListView
from django.db.models import Q

from mwana.apps.nutrition.views import DISTRICTS, get_report_criteria
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.locations.models import Location


def remindmi_graphs(queryset, places):
    graph_data = []
    for place in places:
        site_data = [place]
        site_data.append(queryset.filter(
            Q(cba_conn__contact__location__name=place) |
            Q(cba_conn__contact__location__parent__name=place) |
            Q(cba_conn__contact__location__parent__parent__name=place)).count())
        graph_data.append(site_data)
    return graph_data


def facility_graphs(queryset, places):
    graph_data = []
    for place in places:
        site_data = [place]
        site_data.append(queryset.filter(
            Q(cba_conn__contact__location__name=place) |
            Q(cba_conn__contact__location__parent__name=place)).count())
        graph_data.append(site_data)
    return graph_data


def get_district_facilities():
    district_facilities = {}
    for district in sorted(DISTRICTS):
        clinic = Q(parent__name=district)
        dist = Q(parent__parent__name=district)
        location_data = Location.objects.exclude(type=13).filter(clinic | dist)
        facilities = []
        for i in location_data:
            if i.name not in facilities:
                facilities.append(i.name)
            district_facilities[district] = \
                            sorted([str(unicode(item)) for item in facilities])
    return district_facilities


def malawi_reports(request):
    template_name = "remindmi/malawi_reports.html"
    location, startdate, enddate = get_report_criteria(request)
    selected_location = str(location)
    locations = sorted(DISTRICTS)
    remindmis = PatientEvent.objects.filter(Q(date_logged__gte=startdate),
                                        Q(date_logged__lte=enddate)).order_by('-date')
    mothers = remindmis.filter(event__name="Care program")
    children = remindmis.filter(event__name="Birth")
    if selected_location == "All Districts":
        mother_count = remindmi_graphs(mothers, locations)
        child_count = remindmi_graphs(children, locations)
    else:
        facilities = get_district_facilities()[selected_location]
        mother_count = facility_graphs(mothers, facilities)
        child_count = facility_graphs(children, facilities)
    context = {'mother_count': mother_count, 'child_count': child_count,
               'selected_location': selected_location, 'startdate': startdate,
               'enddate': enddate, 'districts': locations}
    return render_to_response(template_name, context,
        context_instance=RequestContext(request))


def csv_mother_count(request):
    headers = ['Clinic', 'Patient', 'Event', 'Date']
    keys = ['cba_conn.contact.clinic', 'patient', 'event', 'date']
    location, startdate, enddate = get_report_criteria(request)
    mother_count = PatientEvent.objects.filter(Q(date_logged__gte=startdate),\
                            Q(date_logged__lte=enddate), Q(event__name="Care program"))
    if location != "All Districts":
        mother_count = mother_count.filter(\
                Q(cba_conn__contact__location__parent__name=location) |\
                Q(cba_conn__contact__location__parent__parent__name=location))
    return export(headers, keys, mother_count, 'mother_count.csv')


def csv_child_count(request):
    headers = ['Clinic', 'Patient', 'Event', 'Date']
    keys = ['cba_conn.contact.clinic', 'patient', 'event', 'date']
    location, startdate, enddate = get_report_criteria(request)
    child_count = PatientEvent.objects.filter(Q(date_logged__gte=startdate),\
                                Q(date_logged__lte=enddate), Q(event__name="Birth"))
    if location != "All Districts":
        child_count = child_count.filter(\
                Q(cba_conn__contact__location__parent__name=location) |\
                Q(cba_conn__contact__location__parent__parent__name=location))
    return export(headers, keys, child_count, 'child_count.csv')


def export(headers, keys, objects, file_name):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name

    writer = csv.writer(response)
    # column labels
    writer.writerow(headers)
    for obj in objects:
        row = []
        sep = "."
        for key in keys:
            if isinstance(obj, dict) and key in obj:
                row.append(obj[key])
            elif hasattr(obj, key):
                row.append(getattr(obj, key))
            elif sep in key:
                # assuming cba_conn, clean this up later.
                list = key.split(sep)
                if hasattr(obj.cba_conn.contact, list[2]):
                    row.append(getattr(obj.cba_conn.contact, list[2]))
            else:
                row.append("None")
        writer.writerow(row)

    return response
