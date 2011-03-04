# vim: ai ts=4 sts=4 et sw=4
import json
from datetime import datetime, timedelta, date
import logging

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelForm
from django.db import transaction
from django.template import RequestContext
from django.shortcuts import render_to_response

from mwana.apps.labresults import models as labresults
from mwana.decorators import has_perm_or_basicauth
from mwana.apps.locations.models import Location


def text_date(text):
    delimiters = ('-', '/')
    for delim in delimiters:
        text = text.replace(delim, ' ')
    a, b, c = text.split()
    if len(a) == 4:
        return date(int(a), int(b), int(c))
    else:
        return date(int(c), int(b), int(a))


@require_GET
def malawi_reports(request, location=None):
    from webreports.reportcreator import MalawiReports

    today = datetime.today().date()
    try:
        startdate1 = text_date(request.REQUEST['startdate'])
    except (KeyError, ValueError, IndexError):
        startdate1 = today - timedelta(days=30)

    try:
        enddate1 = text_date(request.REQUEST['enddate'])
    except (KeyError, ValueError, IndexError):
        enddate1 = datetime.today().date()
    startdate = min(startdate1, enddate1, datetime.today().date())
    enddate = min(max(enddate1, startdate1), datetime.today().date())

    try:
        district = request.REQUEST['location']
    except (KeyError, ValueError, IndexError):
        district = "All Districts"

    r = MalawiReports()
    res = r.dbsr_tested_retrieved_report(startdate, enddate, district)

    min_turnaround_time, max_turnaround_time, num_of_rsts, num_of_facilities,\
    turnaround_time = r.dbs_avg_turnaround_time_report(startdate, enddate)

    pending = r.dbsr_pending_results_report(startdate, enddate, district)

    districts = r.get_live_districts()

    births = r.reminders_patient_events_report(startdate, enddate)

    single_bar_length, tt_in_graph, graph = r.dbs_graph_data(startdate,
                                                             enddate)

    percent_positive_country, percent_negative_country, \
    percent_rejected_country, percent_positive_provinces, \
    percent_negative_provinces, percent_rejected_provinces, total_dbs, \
    months_reporting, days_reporting, year_reporting = r.dbs_positivity_data()

    return render_to_response('reports/malawi.html',
        {'startdate': startdate,
         'enddate': enddate,
         'today': today,
         'sent_results_rpt': res,
         'districts': districts,
         'selected_location': district,
         'turnaround_time_rpt': turnaround_time,
         'min_turnaround_time': min_turnaround_time,
         'max_turnaround_time': max_turnaround_time,
         'num_of_results': num_of_rsts,
         'num_of_facilities': num_of_facilities,
         'births_rpt': births,
         'formattedtoday': today.strftime("%d %b %Y"),
         'formattedtime': datetime.today().strftime("%I:%M %p"),
         'graph': graph,
         'single_bar_length': single_bar_length,
         'tt_in_graph': tt_in_graph,
         'pending_results': pending,
         'percent_positive_country': percent_positive_country,
         'percent_negative_country': percent_negative_country,
         'percent_rejected_country': percent_rejected_country,
         'percent_positive_provinces': percent_positive_provinces,
         'percent_negative_provinces': percent_negative_provinces,
         'percent_rejected_provinces': percent_rejected_provinces,
         'total_dbs': total_dbs,
         'months_reporting': months_reporting,
         'days_reporting': days_reporting,
         'year_reporting': year_reporting,
     }, context_instance=RequestContext(request))


@require_GET
def zambia_reports(request):
#    , startdate=datetime.today().date()-timedelta(days=30),
#                    enddate=datetime.today().date(
    from webreports.reportcreator import Results160Reports

    today = datetime.today().date()
    try:
        startdate1 = text_date(request.REQUEST['startdate'])
    except (KeyError, ValueError, IndexError):
        startdate1 = today - timedelta(days=30)

    try:
        enddate1 = text_date(request.REQUEST['enddate'])
    except (KeyError, ValueError, IndexError):
        enddate1 = datetime.today().date()
    startdate = min(startdate1, enddate1, datetime.today().date())
    enddate = min(max(enddate1, startdate1), datetime.today().date())

    r = Results160Reports()
    res = r.dbs_sent_results_report(startdate, enddate)

    min_processing_time, max_processing_time, num_of_dbs_processed, \
    num_facs_processing, processing_time =\
    r.dbs_avg_processing_time_report(startdate, enddate)

    min_entering_time, max_entering_time, num_of_rsts_entered, \
    num_facs_entering, entering_time =\
    r.dbs_avg_entering_time_report(startdate, enddate)

    min_retrieval_time, max_retrieval_time, num_of_dbs_retrieved, \
    num_facs_retrieving, retrieval_time =\
    r.dbs_avg_retrieval_time_report(startdate, enddate)

    min_turnaround_time, max_turnaround_time, num_of_rsts, num_of_facilities,\
    turnaround_time = r.dbs_avg_turnaround_time_report(startdate, enddate)

    min_transport_time, max_transport_time, num_of_dbs, num_of_facs,\
    transport_time = r.dbs_avg_transport_time_report(startdate, enddate)

    samples_reported = r.dbs_sample_notifications_report(startdate, enddate)

    samples_at_lab = r.dbs_samples_at_lab_report(startdate, enddate)

    pending = r.dbs_pending_results_report(startdate, enddate)

    payloads = r.dbs_payloads_report(startdate, enddate)

    births = r.reminders_patient_events_report(startdate, enddate)

    single_bar_length, tt_in_graph, graph = r.dbs_graph_data(startdate,
                                                             enddate)

    percent_positive_country, percent_negative_country, \
    percent_rejected_country, percent_positive_provinces, \
    percent_negative_provinces, percent_rejected_provinces, total_dbs, \
    months_reporting, days_reporting, year_reporting = r.dbs_positivity_data()

    return render_to_response('reports/zambia.html',
        {'startdate': startdate,
         'enddate': enddate,
         'today': today,
         'sent_results_rpt': res,
         'turnaround_time_rpt': turnaround_time,
         'min_turnaround_time': min_turnaround_time,
         'max_turnaround_time': max_turnaround_time,
         'num_of_results': num_of_rsts,
         'num_of_facilities': num_of_facilities,
         'processing_time_rpt': processing_time,
         'min_processing_time': min_processing_time,
         'max_processing_time': max_processing_time,
         'num_of_dbs_processed': num_of_dbs_processed,
         'num_facs_processing': num_facs_processing,
         'retrieval_time_rpt': retrieval_time,
         'min_retrieving_time': min_retrieval_time,
         'max_retrieving_time': max_retrieval_time,
         'num_of_dbs_retrieved': num_of_dbs_retrieved,
         'num_facs_retrieving': num_facs_retrieving,
         'entering_time_rpt': entering_time,
         'min_entering_time': min_entering_time,
         'max_entering_time': max_entering_time,
         'num_of_rsts_entered': num_of_rsts_entered,
         'num_facs_entering': num_facs_entering,
         'transport_time_rpt': transport_time,
         'min_transport_time': min_transport_time,
         'max_transport_time': max_transport_time,
         'num_of_dbs': num_of_dbs,
         'num_of_facs': num_of_facs,
         'samples_reported_rpt': samples_reported,
         'samples_at_lab_rpt': samples_at_lab,
         'pending_results': pending,
         'payloads_rpt': payloads,
         'births_rpt': births,
         'formattedtoday': today.strftime("%d %b %Y"),
         'formattedtime': datetime.today().strftime("%I:%M %p"),
         'graph': graph,
         'single_bar_length': single_bar_length,
         'tt_in_graph': tt_in_graph,
         'percent_positive_country': percent_positive_country,
         'percent_negative_country': percent_negative_country,
         'percent_rejected_country': percent_rejected_country,
         'percent_positive_provinces': percent_positive_provinces,
         'percent_negative_provinces': percent_negative_provinces,
         'percent_rejected_provinces': percent_rejected_provinces,
         'total_dbs': total_dbs,
         'months_reporting': months_reporting,
         'days_reporting': days_reporting,
         'year_reporting': year_reporting,
     }, context_instance=RequestContext(request))
