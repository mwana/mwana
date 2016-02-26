# vim: ai ts=4 sts=4 et sw=4
"""
A utility for reporting
"""
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from django.core.management.base import LabelCommand


class Command(LabelCommand):
    help = "Updates Reporting table ScaleUpSite"

    def handle(self, *args, **options):
        process2()       

def __del__(self):
    pass


def process():
    for loc in  Location.objects.filter(parent__parent__slug='800000', supportedlocation__supported=True):
        print loc.parent.name, "|", loc.name, "|",
        time_ranges = [[2015, 4], [2015, 5], [2015, 6],
        [2015, 7], [2015, 8], [2015, 9]]
        for times in time_ranges:
            year, month = times
            count = Result.objects.filter(result__in='IRX',
                                            processed_on__month=month,
                                            clinic=loc, processed_on__year=year                                            
                                            ).count()
            print count, "|",
        print ''

def process2():
    def percent(num, denom):
        if num == 0:
            return 0
        return "%s/%s (%s%%)" % (num, denom, int(round((num * 100.0)/denom)))
    
    for loc in  Location.objects.filter(parent__parent__slug='800000', supportedlocation__supported=True):
        print loc.parent.name, "|", loc.name, "|",
        time_ranges = [[2015, 4], [2015, 5], [2015, 6],
        [2015, 7], [2015, 8], [2015, 9]]
        for times in time_ranges:
            year, month = times
            count = Result.objects.filter(result__in='IRX',
                                            processed_on__month=month,
                                            clinic=loc, processed_on__year=year
                                            ).count()
            total = Result.objects.filter(result__in='PNIRX',
                                            processed_on__month=month,
                                            clinic=loc, processed_on__year=year
                                            ).count()
            print percent(count, total), "|",
        print ''
