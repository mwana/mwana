# vim: ai ts=4 sts=4 et sw=4
"""
Prints District, Facility name, Facility Code, Month, Transport time, Processing time, Delays at lab, Retrieval time, Turnaround time
N.B. Uses median instead of mean
"""

from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from datetime import datetime
from datetime import date


MONTH_MAP = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
             9: 'September', 10: 'October', 11: 'November', 12: 'December'}


class Command(LabelCommand):
    help = "Prints Custom UMB Turnaround non-cohort report for given month and year "
    args = "<start-date> <end-date>"
    label = 'Start date and End date, like 2017-01-01 2017-03-31'

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError('Please specify %s' % self.label)
        else:
            process_data((args[0]), (args[1]))


def __del__(self):
    pass


def _median(p_list):
    if not p_list:
        return '-'
    ordered = sorted(item for item in p_list if item)
    if not ordered:
        return '-'
    size = len(ordered)

    # note that lists are zero indexed
    if size % 2 == 0:
        return (ordered[size // 2 - 1] + ordered[size // 2]) / 2.0
    else:
        return ordered[size // 2]


class Expando:
    pass


def get_date(val):
    return datetime.strptime(val, '%Y-%m-%d').date()


def process_data(start, end, group='SMACHT'):
    print "DBS Tested at Lab between %s and %s" % (start, end)
    print "Data as of date:", date.today().strftime('%d-%b-%Y')
    print "Data source: Mwana System"
    print "District| Facility name|Facility Code|Positive|Negative|Rejected|Total"

    all = Result.objects.filter(result__in='PNRXI', clinic__groupfacilitymapping__group__name=group, processed_on__gte=get_date(start)).filter(processed_on__lte=get_date(end))

    positive = all.filter(result='P')
    negative = all.filter(result='N')
    rejected = all.filter(result__in=['R', 'X', 'I'])
    print "Summary:"
    print "All Listed Districts| All Listed Facilities||%s|%s|%s|%s" % (positive.count(), negative.count(), rejected.count(), all.count())
    print "Listing:"
    data = []
    for loc in Location.objects.filter(groupfacilitymapping__group__name=group):
        expando = Expando()
        expando.facility_name = loc.name
        expando.district_name = loc.parent.name
        expando.slug = loc.slug

        expando.positive = positive.filter(clinic=loc).count()
        expando.negative = negative.filter(clinic=loc).count()
        expando.rejected = rejected.filter(clinic=loc).count()
        expando.total = all.filter(clinic=loc).count()
        data.append(expando)

    for item in sorted(data, key=lambda x: "%s%s%s" % (x.district_name, x.facility_name, x.slug)):
        print "|".join(str(i) for i in [item.district_name, item.facility_name, item.slug, item.positive, item.negative, item.rejected, item.total])
