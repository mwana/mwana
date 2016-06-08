# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import PayloadAuthorWebUserMapping
from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.const import get_clinic_worker_type
from rapidsms.models import Contact
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
        global dbsr_startdate
        dbsr_startdate = datetime(startdate.year, startdate.month,
                                  startdate.day)
    if enddate:
        global dbsr_enddate
        dbsr_enddate = \
            datetime(enddate.year, enddate.month, enddate.day) \
            + timedelta(days=1) - timedelta(seconds=0.01)


def _ready_to_receive_results_via_sms(slug):
    # @type result Result
    if not slug:
        return False
    return "Yes" if Contact.active.filter(location__slug=slug, types=get_clinic_worker_type(),
                                          connection__identity__startswith='+26097').exists() else "No"


def _can_view_results(user):
    return PayloadAuthorWebUserMapping.objects.filter(web_user=user).exists()


def get_viral_load_data(province=None, district=None, facility=None, startdate=None, enddate=None, search_key=None,
                        page=1, test_type=const.get_viral_load_type(), user=None):
    """
    Returns censored message logs (with Requisition IDs, Results hidden)
    """
    can_view_results = _can_view_results(user)
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
    results = results1 | results2

    results = results.filter(author__author__web_user=user)
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
        if not can_view_results:
            break

        date_reached_moh = _formatted_date_time(record.date_reached_moh)
        # @type record ViralLoadView
        original_facility = record.original_facility
        clinic = record.facility_name
        guspec = record.guspec
        ptid = record.ptid
        date_facility_retrieved_result = _formatted_date_time(record.date_facility_retrieved_result)
        who_retrieved = record.who_retrieved
        date_participant_notified = _formatted_date_time(record.date_sms_sent_to_participant)
        text = record.result
        source = record.data_source
        collected_on = record.specimen_collection_date
        date_of_first_notification = _formatted_date_time(record.date_of_first_notification)
        #        nearest_facility = record.nearest_facility_name
        table.append(
            [counter, clinic, original_facility, _ready_to_receive_results_via_sms(record.facility_slug), ptid, guspec,
             collected_on,
             date_reached_moh, date_of_first_notification,
             date_facility_retrieved_result, who_retrieved, date_participant_notified,
             text, source])
        counter = counter + 1

    table.insert(0, ['  #', 'Facility', 'User chosen facility', "Ready to receive results via SMS", 'PTID', 'GUSPEC',
                     'Collected On', 'Date reached MoH', 'Date Clinic first Notified',
                     'Date Facility Got Result', 'Who Retrieved', 'Date Participant Notified',
                     'Result', 'Source'])
    if not can_view_results:
        table.append(['  You', "don't", "have", 'permission', 'to', 'view', 'these',
                      'results.', 'Contact', 'support', 'if you', 'need', 'help'])

    messages_number = records.number
    messages_has_previous = records.has_previous()
    messages_has_next = records.has_next()
    messages_paginator_num_pages = records.paginator.num_pages

    return table, messages_paginator_num_pages, messages_number, messages_has_next, messages_has_previous

