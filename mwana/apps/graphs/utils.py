from datetime import date
from datetime import datetime
from datetime import timedelta

from django.db import connection
from django.db.models import Count
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.reminders.models import PatientEvent


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
            if row[0] in category_names or row[-2] in category_names or row[-1] in category_names:
                transport.append(float(row[1]))
                processing.append(float(row[2]))
                delays.append(float(row[3]))
                retrieving.append(float(row[4]))
            if row[0] in category_names:
                categories.append(str(row[0]))
            elif row[-2] in category_names:
                categories.append(str(row[-2]))
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

    def get_facility_vs_community(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)       

        return PatientEvent.objects.filter(date_logged__gte=start,
                                           date_logged__lt=end,
                                           patient__location__parent__in=facs,
                                           event__name__iexact='birth').\
            values('event_location_type').\
            annotate(total=Count('id'))

def _turnaround_query(start_date, end_date, province_slug, district_slug, facility_slug):
    """
        Uses raw SQL for performance reasons
    """
    ids = ", ".join("%s" % fac.id for fac in get_dbs_facilities(province_slug, district_slug, facility_slug))

    select_clause  = '''select name, avg(transport_time), avg(processing_time), avg(delays_at_lab), avg(retrieving_time) from (
            SELECT province."name", entered_on-collected_on as transport_time, processed_on - entered_on as processing_time
            ,arrival_date::date-processed_on as delays_at_lab,
            result_sent_date::date - arrival_date::date as retrieving_time'''

    join_clause = ''' FROM labresults_result
            join locations_location as facility on facility.id=clinic_id
            join locations_location as district on district.id = facility.parent_id
            join locations_location as province on province.id = district.parent_id
            where collected_on is not null
            and entered_on is not null
            and processed_on is not null
            and arrival_date is not null
            and extract(year from result_sent_date) = %s
            and extract(month from result_sent_date) = %s
            and facility.id in (-1,''' + ids + ''')
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
    facs = Location.objects.exclude(lab_results=None).\
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
#    facs = Location.objects.exclude(type__slug__in=['province', 'district', 'zone']).exclude(lab_results=None)
    facs = Location.objects.exclude(lab_results=None).\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        facs = facs.filter(slug=facility_slug)
    elif district_slug:
        facs = facs.filter(parent__slug=district_slug)
    elif province_slug:
        facs = facs.filter(parent__parent__slug=province_slug)
    return facs

def get_dbs_facilities(province_slug, district_slug, facility_slug):
    facs = Location.objects.exclude(lab_results=None).\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        facs = facs.filter(slug=facility_slug)
    elif district_slug:
        facs = facs.filter(parent__slug=district_slug)
    elif province_slug:
        facs = facs.filter(parent__parent__slug=province_slug)
    return facs