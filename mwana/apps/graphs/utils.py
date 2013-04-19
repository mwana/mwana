from mwana.const import get_zone_type
from mwana.const import ZONE_SLUGS
from mwana.apps.locations.models import Location
from datetime import datetime
from datetime import timedelta

from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result

def get_facilities(province_slug, district_slug, facility_slug):
#    facs = Location.objects.exclude(type__slug__in=['province', 'district', 'zone']).exclude(lab_results=None)
    facs = Location.objects.exclude(lab_results=None)
    if facility_slug:
        facs = facs.filter(slug=facility_slug)
    elif district_slug:
        facs = facs.filter(parent__slug=district_slug)
    elif province_slug:
        facs = facs.filter(parent__parent__slug=province_slug)
    return facs

class GraphServive:
    def get_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start = datetime(start_date.year, start_date.month, start_date.day)
        end = datetime(end_date.year, end_date.month, end_date.day)\
            + timedelta(days=1)

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

