# vim: ai ts=4 sts=4 et sw=4

import os.path

import os

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand

class Command(LabelCommand):
    help = "Loads locations from the specified csv file."
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
    # give django some time to bootstrap itself
    from mwana.apps.locations.models import LocationType, Location, Point
    if not os.path.exists(file_path):
        raise CommandError("Invalid file path: %s." % file_path)


    csv_file = open(file_path, 'r')

    count = 0
    for line in csv_file:
        district_type = LocationType.objects.get(slug="districts")
        code, facility_name, facility_type, district_name = (i.strip() for i in line.split(","))

       
        try:
            district = Location.objects.get(name=district_name, type=district_type)
        except Location.DoesNotExist:
            print district_name, ' district does not exist'
            continue
            
        try:
            facility_type = facility_type.strip()
            type = LocationType.objects.get(slug=clean(facility_type), singular=facility_type)
        except LocationType.DoesNotExist:
            print facility_type, 'type does not exist'
            continue
        try:
            facility = Location.objects.get(slug=code)
            continue
        except Location.DoesNotExist:
            facility = Location(slug=code)

        if not facility.name or facility.name.strip() == '':
            facility.name = facility_name

        if not facility.parent:
            facility.parent = district
        
        facility.type = type
        facility.save()
        count = count + 1

    print "Successfully added %s locations." % count


def clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]