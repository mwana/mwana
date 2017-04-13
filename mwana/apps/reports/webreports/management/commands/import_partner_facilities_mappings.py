# vim: ai ts=4 sts=4 et sw=4

from django.core.management.base import LabelCommand
from mwana.apps.locations.models import Location
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import ReportingGroup
from django.core.management.base import CommandError
import os
from django.core.management.base import LabelCommand



class Command(LabelCommand):
    help = ("creates GroupFacilityMapping's from a csv file")

    args = "<file_path>"
    label = 'valid file path'

    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        file_path = (args[0])
        load_locations(file_path)

    def __del__(self):
        pass



def load_locations(file_path):
    if not os.path.exists(file_path):
        raise CommandError("Invalid file path: %s." % file_path)



    csv_file = open(file_path, 'r')

    count = 0
    initial =  GroupFacilityMapping.objects.all().count()
    for line in csv_file:
        #leave out first line
        if "partner" in line.lower():
            continue
        partner, province_name, district_name, facility_name = line.strip().split(",")

        try:
            facility = Location.objects.get(name=facility_name.strip(), parent__name=district_name.strip())
            group = ReportingGroup.objects.get(name__iexact=partner)
            GroupFacilityMapping.objects.get_or_create(group=group, facility=facility)
        except Exception, e:
            print line.strip(), " - ", e


        count = count + 1

    print "Processed %s locations." % count

    print "Group Facility Mappings. was: %s. Is: %s" % (initial, GroupFacilityMapping.objects.all().count())
