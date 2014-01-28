# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.models import MessageByLocationByBackend
from mwana.apps.reports.models import MessageByLocationByUserType
from mwana.apps.contactsplus.models import ContactType
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.db import connection
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.reminders.models import PatientEvent
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Backend


class GraphServive:

    def get_turnarounds(self, start_date, end_date, province_slug, district_slug, facility_slug):
        """
        Uses plain SQL for performance reasons
        """
        sql = _turnaround_query(start_date, end_date, province_slug, district_slug, facility_slug)
        cursor = connection.cursor()
        cursor.execute(sql, [end_date.year, end_date.month])
        category_names = get_category_data(province_slug, district_slug, facility_slug)

        rows = cursor.fetchall()

        transport = []
        processing = []
        delays = []
        retrieving = []
        categories = []
        for row in rows:
            if row[0] in category_names or row[-1] in category_names:
                transport.append(float(row[1]))
                processing.append(float(row[2]))
                delays.append(float(row[3]))
                retrieving.append(float(row[4]))
            if row[0] in category_names:
                categories.append(str(row[0]))
            elif row[-1] in category_names:
                categories.append(str(row[-1]))

        return categories, transport, processing, delays, retrieving

    def get_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        labs = Payload.objects.values_list('source').all().distinct()
        results = Result.objects.filter(payload__incoming_date__gte=start,
                                        payload__incoming_date__lt=end,
                                        clinic__in=facs)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for lab in sorted(labs):
            data[lab[0]] = []
        time_ranges = []
        while my_date <= end_date:
            for lab in sorted(labs):
                data[lab[0]].append(results.filter(
                                    payload__incoming_date__year=my_date.year,
                                    payload__incoming_date__month=my_date.month,
                                    payload__incoming_date__day=my_date.day,
                                    payload__source=lab[0]
                                    ).count())
            time_ranges.append(my_date.strftime('%d %b'))
            my_date = my_date + timedelta(days=1)

        return time_ranges, data

    def get_monthly_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        labs = Payload.objects.values_list('source').all().distinct()
        results = Result.objects.filter(payload__incoming_date__gte=start,
                                        payload__incoming_date__lt=end,
                                        clinic__in=facs)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for lab in sorted(labs):
            data[lab[0]] = []

        month_ranges = []
        while my_date <= end_date:
            for lab in sorted(labs):
                data[lab[0]].append(results.filter(
                                    payload__incoming_date__year=my_date.year,
                                    payload__incoming_date__month=my_date.month,
                                    payload__source=lab[0]
                                    ).count())
            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_birth_trends(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        trend_items = ['Facility births', 'Community births', 'Unspecified']
        births = PatientEvent.objects.filter(Q(date__gte=start),
                                             Q(date__lt=end),
                                             (Q(patient__location__parent__in=facs) |
                                             Q(patient__location__in=facs))
                                             )

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(trend_items):
            data[item] = []

        births_map = {'Facility births':'cl', 'Community births':'hm', 'Unspecified':None}

        month_ranges = []
        while my_date <= end_date:
            for item in sorted(trend_items):
                data[item].append(births.filter(
                                  date__year=my_date.year,
                                  date__month=my_date.month,
                                  event_location_type=births_map[item]
                                  ).count())
            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_scheduled_visit_trends(self, start_date, end_date,
    province_slug, district_slug, facility_slug, visit_type="6 day", data_type="count"):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        trend_map = {'Mother not Reminded by CBA': ['new'],
                        'Mother  reminded by CBA': ['told', 'confirmed'],
                        'Mother  has gone to clinic': ['confirmed'],
                        " Total Births": ['new', 'told', 'confirmed'],
                        }
        trend_items = [key for key in trend_map]
        
        reminders = PatientTrace.objects.filter(Q(start_date__gte=start),
                                             Q(start_date__lt=end),
                                             Q(initiator='automated_task'),
                                             Q(type=visit_type),
                                             (Q(patient_event__patient__location__parent__in=facs) |
                                             Q(patient_event__patient__location__in=facs))
                                             )

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(trend_items):
            data[item] = []

        month_ranges = []

        while my_date <= end_date:
            divisor = 1
            if data_type.lower() == "percentage":
                divisor = reminders.filter(
                                  start_date__year=my_date.year,
                                  start_date__month=my_date.month,
                                  status__in=['new', 'told', 'confirmed']
                                  ).count()/100.0
            for item in sorted(trend_items):
                data[item].append(round(reminders.filter(
                                  start_date__year=my_date.year,
                                  start_date__month=my_date.month,
                                  status__in=trend_map[item]
                                  ).count()/(divisor or 1), 1))

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)
        
        return month_ranges, data

    def get_monthly_turnaround_trends(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        trend_items = ['Turnaround Time', '1. Transport Time', '2. Processing Time',
        '3. Delays at Lab', '4. Retrieval Time']

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(trend_items):
            data[item] = []

        results = Result.objects.filter(clinic__in=facs, notification_status='sent')

        month_ranges = []
        while my_date <= end_date:
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    collected_on__lte=F('result_sent_date')
                                    )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = 1 + tt_diff + (result.result_sent_date.date() - result.collected_on).days

            data['Turnaround Time'].append(int(tt_diff / tt))

            #Transport Time
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    collected_on__lte=F('entered_on')
                                    )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = tt_diff + (result.entered_on - result.collected_on).days

            data['1. Transport Time'].append(int(tt_diff / tt))

            #Processing Time
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    entered_on__lte=F('processed_on')
                                    )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = 1 + tt_diff + (result.processed_on - result.entered_on).days

            data['2. Processing Time'].append(int(tt_diff / tt))

            #Delays at Lab
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    processed_on__lte=F('arrival_date')
                                    )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = tt_diff + (result.arrival_date.date() - result.processed_on).days

            data['3. Delays at Lab'].append(int(tt_diff / tt))

            #Retrieval Time
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    arrival_date__lte=F('result_sent_date')
                                    )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = 1 + tt_diff + (result.result_sent_date - result.arrival_date).days

            data['4. Retrieval Time'].append(int(tt_diff / tt))

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_results_retrival_trends(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        trend_items = ['Facilities', "Negative", "Positive", "Rejected", 'Total Results']
        for item in sorted(trend_items):
            data[item] = []

        results = Result.objects.filter(clinic__in=facs,
                                        result_sent_date__gte=start,
                                        result_sent_date__lte=end)

        month_ranges = []
        while my_date <= end_date:
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month
                                    )
            neg_res = results.filter(result_sent_date__year=my_date.year,
                                     result_sent_date__month=my_date.month,
                                     result='N'
                                     ).count()
            pos_res = results.filter(result_sent_date__year=my_date.year,
                                     result_sent_date__month=my_date.month,
                                     result='P'
                                     ).count()
            rej_res = results.filter(result_sent_date__year=my_date.year,
                                     result_sent_date__month=my_date.month,
                                     result__in=['R', 'I', 'X']
                                     ).count()

            data['Negative'].append(neg_res)
            data['Positive'].append(pos_res)
            data['Rejected'].append(rej_res)
            data['Total Results'].append(len(tt_res))
            tt_clinics = len(set([res.clinic for res in tt_res]))

            data['Facilities'].append(tt_clinics)

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_messages(self, start_date, end_date,
    province_slug, district_slug, facility_slug, data_type="count", direction='all'):
        use_percentage = "count" != data_type
        field = "count"
        if direction == 'I':
            field = "count_incoming"
        elif direction == 'O':
            field = "count_outgoing"

        start, end = get_datetime_bounds(start_date, end_date)

        groups = Backend.objects.exclude(name__iexact="Message_Tester").values_list('name').all().distinct()
        messages = MessageByLocationByBackend.objects.filter(min_date__gte=start,
                                          min_date__lt=end)

        if any([province_slug, district_slug, facility_slug]):
            facs = get_sms_facilities(province_slug, district_slug, facility_slug)
            messages = MessageByLocationByBackend.objects.filter(min_date__gte=start,
                                          min_date__lt=end, absolute_location__in=facs)


        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(groups):
            data[item[0]] = []

        month_ranges = []

        while my_date <= end_date:
            denom = messages.filter(year=my_date.year,
                        month=my_date.month).aggregate(sum=Sum(field))['sum'] or 0
            for item in sorted(groups):
                if use_percentage:
                    num = messages.filter(year=my_date.year,
                    month=my_date.month,
                    backend=item[0]).aggregate(sum=Sum(field))['sum'] or 0

                    data[item[0]].append(round(100.0 * num/(denom or 1), 1))
                else:
                    data[item[0]].append(
                    messages.filter(year=my_date.year,
                    month=my_date.month,
                    backend=item[0]).aggregate(sum=Sum(field))['sum'] or 0)

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data


    def get_monthly_messages_by_usertype(self, start_date, end_date,
    province_slug, district_slug, facility_slug, data_type="count", direction='all'):
        use_percentage = "count" != data_type
        field = "count"
        if direction == 'I':
            field = "count_incoming"
        elif direction == 'O':
            field = "count_outgoing"

        start, end = get_datetime_bounds(start_date, end_date)

        contact_types = ContactType.objects.exclude(slug='patient').values_list('slug').all().distinct()
        messages = MessageByLocationByUserType.objects.filter(min_date__gte=start,
                                          min_date__lt=end)

        if any([province_slug, district_slug, facility_slug]):
            facs = get_sms_facilities(province_slug, district_slug, facility_slug)
            messages = MessageByLocationByUserType.objects.filter(min_date__gte=start,
                                          min_date__lt=end, absolute_location__in=facs)


        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(contact_types):
            data[item[0]] = []

        month_ranges = []
        
        while my_date <= end_date:
            denom = messages.filter(year=my_date.year,
                        month=my_date.month).aggregate(sum=Sum(field))['sum'] or 0
            for item in sorted(contact_types):                
                if use_percentage:
                    num = messages.filter(year=my_date.year,
                    month=my_date.month,
                    worker_type=item[0]).aggregate(sum=Sum(field))['sum'] or 0

                    data[item[0]].append(round(100.0 * num/(denom or 1), 1))
                else:
                    data[item[0]].append(
                    messages.filter(year=my_date.year,
                    month=my_date.month,
                    worker_type=item[0]).aggregate(sum=Sum(field))['sum'] or 0)


            
            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_facility_vs_community(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        return PatientEvent.objects.filter(date__gte=start,
                                           date__lt=end,
                                           patient__location__parent__in=facs,
                                           event__name__iexact='birth').\
            values('event_location_type').\
            annotate(total=Count('id'))

def _turnaround_query(start_date, end_date, province_slug, district_slug, facility_slug):
    """
        Uses raw SQL for performance reasons. Works on PostgreSql database
    """
    ids = ", ".join("%s" % fac.id for fac in get_dbs_facilities(province_slug, district_slug, facility_slug))
    if not ids:
        ids = '-1'

    select_clause  = '''select name, avg(transport_time), avg(processing_time), avg(delays_at_lab), avg(retrieving_time) from (
            SELECT province."name", entered_on-collected_on as transport_time, processed_on - entered_on as processing_time
            ,arrival_date::date-processed_on as delays_at_lab,
            result_sent_date::date - arrival_date::date as retrieving_time'''

    join_clause = ''' FROM labresults_result
            join locations_location as facility on facility.id=clinic_id
            join locations_location as district on district.id = facility.parent_id
            join locations_location as province on province.id = district.parent_id
            where collected_on <= processed_on
            and entered_on <= processed_on
            and arrival_date >= processed_on
            and notification_status <> 'obsolete'
            and extract(year from result_sent_date) = %s
            and extract(month from result_sent_date) = %s
            and facility.id in (''' + ids + ''')
            ) a
            '''

    aggregate_clause = '''
            group by name
            order by name
            '''

    if province_slug or district_slug or facility_slug:
        select_clause = select_clause.replace('from (', ', district from (') + ', district."name" as district'
        aggregate_clause = '''
            group by name, district
            order by district
            '''

    if district_slug or facility_slug:
        select_clause = select_clause.replace('from (', ', facility from (')  + ', facility.name as facility'
        aggregate_clause = '''group by name, district, facility
            order by facility
            '''

    return select_clause + join_clause + aggregate_clause

def get_category_data(province_slug, district_slug, facility_slug):
    facs = Location.objects.filter(supportedlocation__supported=True).exclude(lab_results=None).\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        return [loc.name for loc in facs.filter(slug=facility_slug)]
    elif district_slug:
        return list(set([loc.name for loc in facs.filter(parent__slug=district_slug)]))
    elif province_slug:
        return list(set([loc.parent.name for loc in facs.filter(parent__parent__slug=province_slug)]))
    else:
        return list(set([loc.parent.parent.name for loc in facs.all()]))


def get_datetime_bounds(start_date, end_date):
    return datetime(start_date.year, start_date.month, start_date.day), \
        datetime(end_date.year, end_date.month, end_date.day) + \
        timedelta(days=1)

def get_facilities(province_slug, district_slug, facility_slug):
    facs = Location.objects.filter(supportedlocation__supported=True).\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        facs = facs.filter(slug=facility_slug)
    elif district_slug:
        facs = facs.filter(parent__slug=district_slug)
    elif province_slug:
        facs = facs.filter(parent__parent__slug=province_slug)
    return facs

def get_sms_facilities(province_slug, district_slug, facility_slug):
    facs = Location.objects.all().\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        facs = facs.filter(Q(slug=facility_slug) | Q(parent__slug=facility_slug))
    elif district_slug:
        facs = facs.filter(Q(parent__parent__slug=district_slug) | Q(parent__slug=district_slug) | Q(slug=district_slug))
    elif province_slug:
        facs = facs.filter(Q(parent__parent__parent__slug=province_slug) | Q(parent__parent__slug=province_slug) | Q(parent__slug=province_slug) | Q(slug=province_slug))
    return facs

def get_dbs_facilities(province_slug, district_slug, facility_slug):
    return get_facilities(province_slug, district_slug, facility_slug).exclude(lab_results=None)
