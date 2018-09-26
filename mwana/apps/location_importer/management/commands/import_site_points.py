# vim: ai ts=4 sts=4 et sw=4

import os.path

import os

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand

class Command(LabelCommand):
    help = "Loads coordinates from the specified csv file."
    args = "<file_path>"
    label = 'valid file path'

    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        file_path = (args[0])
        load_coords(file_path)

    def __del__(self):
        pass

def load_coords(file_path):
    # give django some time to bootstrap itself
    from mwana.apps.locations.models import LocationType, Location, Point
    if not os.path.exists(file_path):
        raise CommandError("Invalid file path: %s." % file_path)

    csv_file = open(file_path, 'r')

    count = 0
    for line in csv_file:
        facility_name, code, longitude, latitude = (i.strip() for i in line.split(","))
       
        try:
            facility_without_coords = Location.objects.get(point=None, slug=code)
            if facility_without_coords.name.split()[0].lower().strip() != facility_name.split()[0].lower().strip():
                print "Mismatch in facilities", code, facility_name, "Old =", facility_without_coords
                continue

            facility_without_coords.point = Point.objects.get_or_create(latitude=latitude, longitude=longitude)[0]
            facility_without_coords.save()
            count = count + 1
        except Location.DoesNotExist:
            if not Location.objects.filter(slug=code).exists():
                pass
#                print code, facility_name, ' district does not exist'
            continue      
    print "Successfully added %s coordinates to locations." % count
