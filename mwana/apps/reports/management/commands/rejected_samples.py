# vim: ai ts=4 sts=4 et sw=4
"""
A utility for reporting
"""
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from django.core.management.base import LabelCommand
from django.core.management.base import CommandError

from datetime import date
from datetime import timedelta

class Command(LabelCommand):
    help = "Prints rejected trends."
    args = "<Province Code> <Number of Months> [P]\n\nP - show output as percentages"
    label = 'valid years'

    def handle(self, * args, ** options):
        if len(args) not in (2, 3):
            raise CommandError('Please specify 2 or 3 parameters. \n%s' % self.args)
        
        num_string = args[1]
        if not num_string.isdigit():
            raise CommandError("%s is not a integer" % num_string)

        code = args[0]
        if len(args) == 3 and args[2].lower() == 'p':
            process2(code, int(num_string))
        else:
            process(code, int(num_string))
         

def __del__(self):
    pass


def _month_ranges(num):
    today = date.today()
    start_date = today - timedelta(days = 30 * num)
    month, year = start_date.month, start_date.year
    while True:
        yield year, month
        if (month, year) == (today.month, today.year):
            return
        month += 1
        if (month > 12):
            month = 1
            year += 1


def process(code, num):
    print "District|Facility|", "|".join("%s_%s" % (x, y) for x, y in _month_ranges(num))
    for loc in  Location.objects.filter(parent__parent__slug__startswith=code, supportedlocation__supported=True):
        print loc.parent.name, "|", loc.name, "|",
        time_ranges = _month_ranges(num)
        for times in time_ranges:
            year, month = times
            count = Result.objects.filter(result__in='IRX',
                                            processed_on__month=month,
                                            clinic=loc, processed_on__year=year                                            
                                            ).count()
            print count, "|",
        print ''


def process2(code, num):
    print "District|Facility|", "|".join("%s_%s" % (x, y) for x, y in _month_ranges(num))
    def percent(num, denom):
        if num == 0:
            return 0
        return "%s/%s (%s%%)" % (num, denom, int(round((num * 100.0)/denom)))
    
    for loc in  Location.objects.filter(parent__parent__slug__startswith=code, supportedlocation__supported=True):
        print loc.parent.name, "|", loc.name, "|",
        time_ranges = _month_ranges(num)
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
