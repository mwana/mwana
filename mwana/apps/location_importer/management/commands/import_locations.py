""" This script imports locations from a csv file into the database.
The csv file should have columns in the order:
Province, District, Facility_Name, Code, Facility Type, Latitude,	Longitude
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
            (slug="provinces", name="Provinces")

    try:
        district_type = LocationType.objects.get(slug="districts")
    except LocationType.DoesNotExist:
        district_type = LocationType.objects.create\
            (slug="districts", name="Districts")

    csv_file = open(file_path, 'r')

    count = 0    
    for line in csv_file:
        #leave out first line
        if "latitude" in line.lower():
            continue
        province_name, district_name, facility_name, code, facility_type, latitude, longitude = line.split(",")

        #create/load province
        try:
            province = Location.objects.get(name=province_name, type=province_type)
        except Location.DoesNotExist:
            province = Location.objects.create(name=province_name, type=province_type, slug=clean(province_name))

        #create/load district
        try:
            district = Location.objects.get(name=district_name, type=district_type)
        except Location.DoesNotExist:
            district = Location.objects.create(name=district_name, type=district_type, slug=clean(district_name), parent=province)
        #create/load facility type    
        try:
            facility_type = facility_type.strip()
            type = LocationType.objects.get(slug=clean(facility_type), name=facility_type)
        except LocationType.DoesNotExist:
            type = LocationType.objects.create(slug=clean(facility_type), name=facility_type)
        #create/load facility
        try:
            facility = Location.objects.get(slug=code)
        except Location.DoesNotExist:
            facility = Location(slug=code)
        facility.name = facility_name
        facility.parent = district
        facility.point = Point.objects.get_or_create(latitude=latitude, longitude=longitude)[0]
        facility.type = type
        facility.save()
        count += 1



        
   
    print "Successfully processed %s locations." % count



def _new_facility_name():
    from mwana.apps.locations.models import Location
    name = "%s %s" % (random.choice(PLACES_IN_ZAMBIA), 
                      random.choice(HEALTH_CENTER_TYPES))
    try:
        Location.objects.get(name=name)
        return _new_facility_name()
    except Location.DoesNotExist:
        return name

            
def clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]