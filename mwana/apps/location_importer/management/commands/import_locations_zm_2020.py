# vim: ai ts=4 sts=4 et sw=4
""" This script imports locations from a csv file into the database.
The csv file should have columns in the order:
Province, District, Facility_Name, Code, Facility Type, Latitude, Longitude
"""
import os.path

import os
import random
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

    try:
        province_type = LocationType.objects.get(slug="provinces")
    except LocationType.DoesNotExist:
        province_type = LocationType.objects.create\
            (slug="provinces", singular="Province", plural="Provinces")

    try:
        district_type = LocationType.objects.get(slug="districts")
    except LocationType.DoesNotExist:
        district_type = LocationType.objects.create\
            (slug="districts", singular="district", plural="districts")

    csv_file = open(file_path, 'r')

    count = 0
    for line in csv_file:
        #leave out first line
        if "latitude" in line.lower():
            continue
        print line
        province_name, district_name, facility_name, code, facility_type, latitude, longitude = line.split(",")

        province = Location.objects.get(name=province_name, type=province_type)
        

        try:
            district = Location.objects.get(name=district_name,
                                                type=district_type)
        except Location.DoesNotExist:
            district = Location.objects.create(name=district_name,
                                                   type=district_type,
                                                   slug=code[:-1] + '0',
                                                   parent=province)
        facility_type = facility_type.strip()
        type = LocationType.objects.get(slug=clean(facility_type), singular=facility_type)

        try:
            facility = Location.objects.get(slug=code.lower())
        except Location.DoesNotExist:
            facility = Location(slug=code.lower())

        if not facility.name or facility.name.strip() == '':
            facility.name = facility_name

        if not facility.parent:
            facility.parent = district

        if not facility.point and latitude and longitude:
            facility.point = Point.objects.get_or_create(latitude=latitude, longitude=longitude)[0]

        facility.type = type
        facility.save()
#        print (facility_name)

        count += 1


    print "Successfully processed %s locations." % count


def clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]