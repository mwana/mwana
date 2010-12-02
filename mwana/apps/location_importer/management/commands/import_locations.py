# vim: ai ts=4 sts=4 et sw=4
""" This script imports locations from a csv file into the database.
The csv file should have columns in the order:
Province, District, Facility_Name, Code, Facility Type, Latitude, Longitude
"""
import os
import csv
import random
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from django.db import transaction


class Command(LabelCommand):
    help = """Loads locations from the specified CSV file.  The columns in the
CSV file must appear in the following order, and include no header in the
first row:

    Province, District, Facility_Name, Code, Facility Type, Latitude, Longitude

Province and District are optional, but the columns must still exist."""
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
    if not os.path.exists(file_path):
        raise CommandError("Invalid file path: %s." % file_path)


def _province_type():
    """Fetches or creates, and returns the province location type."""
    from mwana.apps.locations.models import LocationType
    try:
        province_type = LocationType.objects.get(slug="provinces")
    except LocationType.DoesNotExist:
        province_type = LocationType.objects.create\
            (slug="provinces", singular="Province", plural="Provinces")
    return province_type


def _district_type():
    """Fetches or creates, and returns the district location type."""
    from mwana.apps.locations.models import LocationType
    try:
        district_type = LocationType.objects.get(slug="districts")
    except LocationType.DoesNotExist:
        district_type = LocationType.objects.create\
            (slug="districts", singular="district", plural="districts")
    return district_type


@transaction.commit_on_success
def load_locations(file_path):
    # give django some time to bootstrap itself
    from mwana.apps.locations.models import LocationType, Location, Point
    if not os.path.exists(file_path):
        raise CommandError("Invalid file path: %s." % file_path)

    csv_file = csv.reader(open(file_path, 'r'))

    count = 0    
    for line in csv_file:
        province_name, district_name, facility_name, code, facility_type,\
                                                     latitude, longitude = line
        #leave out first line
        if "latitude" in latitude:
            continue
        
        province_type = None
        if province_name:
            #create/load province
            # only create the type if we actually have a province record
            if not province_type:
                province_type = _province_type()
            try:
                province = Location.objects.get(name=province_name,
                                                type=province_type)
            except Location.DoesNotExist:
                province = Location.objects.create(name=province_name,
                                                   type=_province_type,
                                                   slug=clean(province_name))
        else:
            province = None
        district_type = None
        if district_name:
            #create/load district
            # only create the type if we actually have a district record
            if not province_type:
                district_type = _district_type()
            try:
                district = Location.objects.get(name=district_name,
                                                type=district_type)
            except Location.DoesNotExist:
                district = Location.objects.create(name=district_name,
                                                   type=district_type,
                                                   slug=clean(district_name),
                                                   parent=province)
        else:
            district = None
        #create/load facility type    
        try:
            facility_type = facility_type.strip()
            type = LocationType.objects.get(slug=clean(facility_type),
                                            singular=facility_type)
        except LocationType.DoesNotExist:
            type = LocationType.objects.create(slug=clean(facility_type),
                                               singular=facility_type,
                                               plural=facility_type + "s")
        #create/load facility
        try:
            facility = Location.objects.get(slug=code)
        except Location.DoesNotExist:
            facility = Location(slug=code)
        facility.name = facility_name
        facility.parent = district
        if latitude and longitude:
            facility.point, _ = Point.objects.get_or_create(latitude=latitude,
                                                            longitude=longitude)
        facility.type = type
        facility.save()
        count += 1
    print "Successfully processed %s locations." % count


def clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]
