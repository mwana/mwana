# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import timedelta

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.graphs.utils import GraphService
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_month_end
from mwana.apps.reports.utils.htmlhelper import get_month_start
from mwana.apps.reports.utils.htmlhelper import get_rpt_districts
from mwana.apps.reports.utils.htmlhelper import get_rpt_facilities
from mwana.apps.reports.utils.htmlhelper import get_rpt_provinces
from mwana.apps.reports.utils.htmlhelper import read_date_or_default
from mwana.apps.reports.views import read_request
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


def graphs(request):
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")
    return render_to_response('graphs/graphs.html',
                              {
                              "fstart_date": start_date.strftime("%Y-%m-%d"),
                              "fend_date": end_date.strftime("%Y-%m-%d"),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", get_rpt_provinces(request.user), rpt_provinces),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", get_rpt_districts(request.user), rpt_districts),
                              'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", get_rpt_facilities(request.user), rpt_facilities),

                              }, context_instance=RequestContext(request)
                              )

def trivial_graphs(request):
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")
    return render_to_response('graphs/trivial_graphs.html',
                              {
                              "fstart_date": start_date.strftime("%Y-%m-%d"),
                              "fend_date": end_date.strftime("%Y-%m-%d"),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", get_rpt_provinces(request.user), rpt_provinces),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", get_rpt_districts(request.user), rpt_districts),
                              'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", get_rpt_facilities(request.user), rpt_facilities),

                              }, context_instance=RequestContext(request)
                              )


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

def lab_submissions(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date = min(max(enddate1, startdate1, MWANA_ZAMBIA_START_DATE), date.today())
    start_date = end_date - timedelta(days=30)

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_lab_submissions(start_date, end_date, rpt_provinces\
                                                    , rpt_districts,
                                                    rpt_facilities)
    
    for k, v in data.items():
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/lab_submissions.html',
                              {
                              "x_axis":time_ranges,
                              "title": "'Daily Laboratory DBS Submissions to Mwana'",
                              "sub_title": "'Period: %s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'DBS samples'",
                              "report_data": report_data,
                              }, context_instance=RequestContext(request)
                              )

def monthly_lab_submissions(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_lab_submissions(start_date, end_date, rpt_provinces\
                                                            , rpt_districts,
                                                            rpt_facilities)

    for k, v in data.items():
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)
    
    return render_to_response('graphs/lab_submissions.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly Laboratory DBS Submissions to Mwana'",
                              "sub_title": "'Period: %s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'DBS samples'",
                              "report_data": report_data,
                              }, context_instance=RequestContext(request)
                              )

def monthly_birth_trends(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date = min(max(enddate1, startdate1, MWANA_ZAMBIA_START_DATE), date.today())
    start_date = end_date - timedelta(days=30 * monthrange)

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_birth_trends(start_date, end_date,
                                                         rpt_provinces
                                                         , rpt_districts,
                                                         rpt_facilities)

    for k, v in sorted(data.items()):
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)
   
    return render_to_response('graphs/lab_submissions.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly Birth Trends'",
                              "sub_title": "'Period: %s  to %s (Filtered by Date of Birth)'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'# of Births'",
                              "report_data": report_data,
                              }, context_instance=RequestContext(request)
                              )

def monthly_scheduled_visit_trends(request):
    visit_type = read_request(request, "visit_type") or "6 day"
    data_type = read_request(request, "data_type") or "percentage"
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_scheduled_visit_trends(start_date, end_date,
                                                                   rpt_provinces
                                                                   , rpt_districts,
                                                                   rpt_facilities, visit_type, data_type)

    for k, v in reversed(sorted(data.items())):
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/lab_submissions.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'%s Visit Trend'" % visit_type.title(),
                              "sub_title": "' (Filtered by Postanatal Date) **Note that TOLD and CONFIRMED may be under-reported'",
                              "label_y_axis": "'%s'" % (data_type.title()),
                              "report_data": report_data,
                              "skip_total": True,
                              }, context_instance=RequestContext(request)
                              )

def monthly_turnaround_trends(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_turnaround_trends(start_date, end_date,
                                                              rpt_provinces
                                                              , rpt_districts,
                                                              rpt_facilities)

    for k, v in sorted(data.items()):
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/messages.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly DBS Turnaround Trends'",
                              "sub_title": "'Period: %s  to %s (Filtered by Results Retreived Date)'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'Days'",
                              "report_data": report_data,
                              "skip_total": True,
                              }, context_instance=RequestContext(request)
                              )

def dbs_testing_trends(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_dbs_testing_trends(start_date, end_date,
                                                              rpt_provinces
                                                              , rpt_districts,
                                                              rpt_facilities)

    for k, v in sorted(data.items()):
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/messages.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly DBS Testing Trends'",
                              "sub_title": "'Period: %s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'Days'",
                              "report_data": report_data,
                              "skip_total": True,
                              }, context_instance=RequestContext(request)
                              )

def monthly_results_retrival_trends(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_results_retrival_trends(start_date, end_date,
                                                                    rpt_provinces
                                                                    , rpt_districts,
                                                                    rpt_facilities)

    for k, v in sorted(data.items()):
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/lab_submissions.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly Results Retrieval Trends'",
                              "sub_title": "'Facilities retrieving results in Period: %s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'Count'",
                              "report_data": report_data,
                              }, context_instance=RequestContext(request)
                              )

def messages(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)
    data_type = read_request(request, "data_type") or "count"
    direction = read_request(request, "direction") or "all"

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_messages(start_date, end_date,
                                                     rpt_provinces
                                                     , rpt_districts,
                                                     rpt_facilities, data_type,
                                                     direction)

    for k, v in data.items():
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/messages.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly SMS\\'s by Backend '",# % {"all":"", "I":"- Incoming", "O":"- Outgoing"}.get(direction),
                              "sub_title": "'Period: %s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'%s of SMS Messages'" % data_type.title(),
                              "report_data": report_data,
                              }, context_instance=RequestContext(request)
                              )

def messages_by_user_type(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)
    data_type = read_request(request, "data_type") or "percentage"
    direction = read_request(request, "direction") or "all"
    
    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_messages_by_usertype(start_date,
                                                                 end_date, rpt_provinces\
                                                                 , rpt_districts,
                                                                 rpt_facilities, data_type, direction)

    for k, v in data.items():
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/messages.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly SMS\\'s by User Type %s'" % {"all":"", "I":"- Incoming", "O":"- Outgoing"}.get(direction),
                              "sub_title": "'Period: %s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'%s'" % data_type.title(),
                              "report_data": report_data,
                              "chart_type": "'spline'",
                              }, context_instance=RequestContext(request)
                              )


def messages_by_partner(request):
    enddate1, rpt_districts, rpt_facilities, rpt_provinces, startdate1, monthrange = get_report_parameters(request)
    end_date, start_date = get_month_range_bounds(enddate1, monthrange, startdate1)
    data_type = read_request(request, "data_type") or "count"
    direction = read_request(request, "direction") or "all"

    service = GraphService()
    report_data = []

    time_ranges, data = service.get_monthly_messages_by_partner(start_date,
                                                                 end_date, rpt_provinces\
                                                                 , rpt_districts,
                                                                 rpt_facilities, data_type, direction)

    for k, v in data.items():
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/stacked_grouped.html',
                              {
                              "x_axis": time_ranges,
                              "title": "'Monthly SMS\\'s by Partner %s'" % {"all":"", "I":"- Incoming", "O":"- Outgoing"}.get(direction),
                              "sub_title": "'Period: %s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'%s'" % data_type.title(),
                              "report_data": report_data,
                              "chart_type": "'column'",
                              }, context_instance=RequestContext(request)
                              )

def facility_vs_community(request):
    enddate1, district_slug, facility_slug, province_slug, startdate1, _ = get_report_parameters(request)

    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, startdate1, MWANA_ZAMBIA_START_DATE), date.today())
    
    service = GraphService()
    
    report_data = []

    for item in service.get_facility_vs_community(start_date, end_date, province_slug, district_slug, facility_slug):
        report_data.append([get_location_type_display(item['event_location_type']), item['total']])

    return render_to_response('graphs/facility_vs_community.html',
                              {
                              "x_axis":[(end_date - timedelta(days=i)).strftime('%d %b') for i in range(30, 0, -1)],
                              "title": "'Facility vs Community Births'",
                              "sub_title": "'Period: %s  to %s (Filtered by Date of Birth)'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'DBS samples'",
                              "report_data": report_data,
                              "series_name": 'Births',
                              }, context_instance=RequestContext(request)
                              )

def messages_by_location(request):
    enddate1, district_slug, facility_slug, province_slug, startdate1, _ = get_report_parameters(request)

    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, startdate1, MWANA_ZAMBIA_START_DATE), date.today())
    report_level = 'province'
    
    service = GraphService()
    
    report_data = []

    report_level, aggregate_function, service_data = service.get_messages_by_location(start_date, end_date, province_slug, district_slug, facility_slug)
    for item in service_data:
        report_data.append([str(item[report_level]), item[aggregate_function]])
    
    return render_to_response('graphs/facility_vs_community.html',
                              {
                              "x_axis":[(end_date - timedelta(days=i)).strftime('%d %b') for i in range(30, 0, -1)],
                              "title": "'Messages by Loaction'",
                              "sub_title": "'Period: %s  to %s'" % (start_date.strftime("%b %Y"), end_date.strftime("%b %Y")),                              
                              "report_data": report_data,
                              "series_name": 'Messages',
                              }, context_instance=RequestContext(request)
                              )


def turnaround(request):
    enddate1, district_slug, facility_slug, province_slug, startdate1, monthrange = get_report_parameters(request)

    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, MWANA_ZAMBIA_START_DATE), date.today())

    service = GraphService()


    categories, transport, processing, delays, retrieving = service.get_turnarounds(start_date, end_date, province_slug, district_slug, facility_slug)
    report_data = []
    rpt_object = Expando()
    rpt_object.key = 'Transport Time'
    rpt_object.value = transport
    report_data.append(rpt_object)
    
    rpt_object = Expando()
    rpt_object.key = 'Processing Time'
    rpt_object.value = processing
    report_data.append(rpt_object)    

    rpt_object = Expando()
    rpt_object.key = 'Delays at Lab'
    rpt_object.value = delays
    report_data.append(rpt_object)

    rpt_object = Expando()
    rpt_object.key = 'Retrieving Time'
    rpt_object.value = retrieving
    report_data.append(rpt_object)

    return render_to_response('graphs/turnaround.html',
                              {
                              "x_axis": categories,
                              "title": "'DBS Turnaround'",
                              "sub_title": "'Month: %s ( (Filtered by Results Retrived Date))'" % (end_date.strftime("%b %Y")),
                              "label_y_axis": "'DBS samples'",
                              "transport": transport,
                              "processing": processing,
                              "delays": delays,
                              "retrieving": retrieving,
                              "categories": categories,
                              "report_data": report_data,
                              }, context_instance=RequestContext(request)
                              )
