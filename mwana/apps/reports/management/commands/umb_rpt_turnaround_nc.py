# vim: ai ts=4 sts=4 et sw=4
"""
Prints District, Facility name, Facility Code, Month, Transport time, Processing time, Delays at lab, Retrieval time, Turnaround time
N.B. Uses median instead of mean
"""

from mwana.apps.reports.models import Turnaround
from mwana.apps.locations.models import Location

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand

LOCATION_SLUGS = ['813004', '813001', '813007', '813002', '813011', '813012',
                  '813015', '813014', '801010', '801099', '801038', '801002', '801002', '801019',
                  '801020', '801022', '801039', '801028', '801035', '802099', '804030', '804014',
                  '804034', '804013', '804046', '805010', '805012', '805013', '805026', '805025',
                  '805022', '806019', '806011', '806022', '806003', '806007', '806012', '806013',
                  '806018', '806008', '806010', '806016', '806002', '806025', '806026', '805029',
                  '806010hp', '806017', '806021', '807014', '807048', '807015', '807016',
                  '807017', '807019', '807021', '807021', '807022', '807023', '807024', '807025',
                  '807026', '807027', '807030', '807029', '807055', '807033', '807036', '807037',
                  '807032', '807049', '807038', '807041', '807001', '808016', '808022', '808025',
                  '808014', '808030', '808011', '808013', '808001', '811013', '811001', '804012',
                  '804031', '801016', '801025', '801026']

MONTH_MAP = {1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}

class Command(LabelCommand):
    help = "Prints Custom UMB Turnaround non-cohort report for given month and year "
    args = "<year> <month>"
    label = 'Year and month, like 2016 3'

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError('Please specify %s' % self.label)
        if not (args[0].isdigit() and args[1].isdigit()):
            raise CommandError('Please specify %s' % self.label)
        else:
            process_data(int(args[0]), int(args[1]))


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


def process_data(year, month):
    print "Number of days processes took to complete in", MONTH_MAP[month], year
    print "District| Facility name|Facility Code|Transporting time|Processing time|Data entry & Delays at lab|Retrieving Results by Facilities"
    all = Turnaround.objects.filter(facility_slug__in=LOCATION_SLUGS)
    
    transport_results = all.filter(received_at_lab__year=year).filter(received_at_lab__month=month)
    processing_results = all.filter(processed_on__year=year).filter(processed_on__month=month)
    delays_results = all.filter(date_reached_moh__year=year).filter(date_reached_moh__month=month)
    retrieving_results = all.filter(date_retrieved__year=year).filter(date_retrieved__month=month)

    data = []
    for loc in Location.objects.filter(slug__in=LOCATION_SLUGS):
        expando = Expando()
        expando.facility_name = loc.name
        expando.district_name = loc.parent.name
        expando.slug = loc.slug
        # @type rec Turnaround
        expando.avg_transport_time = _median([rec.transporting for rec in transport_results.filter(facility_slug=loc.slug)])
        expando.avg_processing_time = _median([rec.processing for rec in processing_results.filter(facility_slug=loc.slug)])
        expando.avg_delay_time = _median([rec.delays for rec in delays_results.filter(facility_slug=loc.slug)])
        expando.avg_retrieving_time = _median([rec.retrieving for rec in retrieving_results.filter(facility_slug=loc.slug)])

        data.append(expando)

    for item in sorted(data, key=lambda x: "%s%s%s" % (x.district_name, x.facility_name, x.slug)):
        # @type item 
        # @type item 
        # @type item 
        print "|".join(str(i) for i in [item.district_name, item.facility_name, item.slug, item.avg_transport_time, item.avg_processing_time, item.avg_delay_time, item.avg_retrieving_time])

     