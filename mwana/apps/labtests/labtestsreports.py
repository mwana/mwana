# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.labtests.models import ViralLoadView
from mwana import const
from datetime import date
from datetime import datetime
from datetime import timedelta

from mwana.apps.locations.models import Location
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


today = date.today()
dbsr_enddate = datetime(today.year, today.month, today.day) + \
        timedelta(days=1) - timedelta(seconds=0.01)
dbsr_startdate = datetime(today.year, today.month, today.day) - \
        timedelta(days=30)


def _formatted_date_time(date):
    try:
        return date.strftime("%Y-%m-%d %H:%M")
    except:
        return date

def set_reporting_period(startdate, enddate):
    if startdate:
        dbsr_startdate = datetime(startdate.year, startdate.month,
                                       startdate.day)
    if enddate:
        dbsr_enddate = \
        datetime(enddate.year, enddate.month, enddate.day)\
        + timedelta(days=1) - timedelta(seconds=0.01)


def get_viral_load_data(province=None, district=None, facility=None, startdate=None, enddate=None, search_key=None, page=1, test_type=const.get_viral_load_type()):
    """
    Returns censored message logs (with Requisition IDs, Results hidden)
    """
    set_reporting_period(startdate, enddate)
    
    locations = Location.objects.exclude(test_results=None)
    
    if facility:
        locations = locations.filter(slug=facility)
    elif district:
        locations = locations.filter(parent__slug=district)
    elif province:
        locations = locations.filter(parent__parent__slug=province)
    slugs = (loc.slug for loc in locations)

    results1 = ViralLoadView.objects.filter(facility_slug__in=slugs, date_reached_moh__gte=dbsr_startdate). \
        filter(date_reached_moh__lte=dbsr_enddate)
    results2 = ViralLoadView.objects.filter(facility_slug=None, date_reached_moh__gte=dbsr_startdate). \
        filter(date_reached_moh__lte=dbsr_enddate)
    results = results1|results2
    if const.get_viral_load_type() == test_type:
        results = results.exclude(test_type=const.get_dbs_type()).order_by("specimen_collection_date")
    elif const.get_dbs_type() == test_type:
        results = results.exclude(test_type=const.get_viral_load_type()).order_by("specimen_collection_date")

    table = []
   
    if not page:
        page = 1

    paginator = Paginator(results, 200)
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        records = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        records = paginator.page(paginator.num_pages)

    counter = records.start_index()
    for record in records.object_list:
        date_reached_moh = _formatted_date_time(record.date_reached_moh)
        # @type record ViralLoadView
        original_facility = record.original_facility
        clinic = record.facility_name
        guspec = record.coded_guspec()
        ptid = record.coded_ptid()
        date_facility_retrieved_result = _formatted_date_time(record.date_facility_retrieved_result)
        who_retrieved = record.coded_who_retrieved()
        date_participant_notified = _formatted_date_time(record.date_sms_sent_to_participant)
        text = record.coded_result()
        source = record.data_source
        collected_on = record.specimen_collection_date
        date_of_first_notification = _formatted_date_time(record.date_of_first_notification)
        nearest_facility = record.nearest_facility_name
        table.append([counter, original_facility, clinic, nearest_facility, ptid, guspec, collected_on,
            date_reached_moh, date_of_first_notification,
                  date_facility_retrieved_result, date_participant_notified,
                  who_retrieved, text, source])
        counter = counter + 1

    table.insert(0, ['  #',  'Original Facility', 'Resolved Facility', 'Nearest Facility', 'PTID', 'GUSPEC', 'Collected On', 'Date reached MoH',
                     'Date Clinic first Notified',
                    'Date Facility Got Result', 'Date Participant Notified','Who Retrieved',
                 'Result', 'Source'])
    messages_number=records.number
    messages_has_previous = records.has_previous()
    messages_has_next = records.has_next()
    messages_paginator_num_pages = records.paginator.num_pages
    
    return table, messages_paginator_num_pages, messages_number, messages_has_next, messages_has_previous

