
from datetime import datetime
from datetime import timedelta

from django.db.models import Count
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.reminders.models import PatientEvent

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

def get_datetime_bounds(start_date, end_date):
    return datetime(start_date.year, start_date.month, start_date.day), \
        datetime(end_date.year, end_date.month, end_date.day) + \
        timedelta(days=1)

class GraphServive:

    def get_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        labs = Payload.objects.values_list('source').all().distinct()
        results = Result.objects.filter(payload__incoming_date__gte=start,
                                        payload__incoming_date__lt=end,
                                        clinic__in=facs)

        my_date = start_date
        data = {}
        for lab in sorted(labs):
            data[lab[0]] = []

        while my_date <= end_date:
            for lab in sorted(labs):
                data[lab[0]].append(results.filter(
                                    payload__incoming_date__year=my_date.year,
                                    payload__incoming_date__month=my_date.month,
                                    payload__incoming_date__day=my_date.day,
                                    payload__source=lab[0]
                                    ).count())
            my_date = my_date + timedelta(days=1)

        return data

    def get_facility_vs_community(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)       

        return PatientEvent.objects.filter(date_logged__gte=start,
                                           date_logged__lt=end,
                                           patient__location__parent__in=facs,
                                           event__name__iexact='birth').\
            values('event_location_type').\
            annotate(total=Count('id'))
       
