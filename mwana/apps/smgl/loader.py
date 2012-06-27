import os
from django.conf import settings
from mwana.apps.locations.models import LocationType, Location, Point

class LoaderException(Exception):
    pass

def load_zones(file_path, log_to_console=True):
    if log_to_console: print "loading static zones from %s" % file_path
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    zone_type = LocationType.objects.get(slug="zone")
    csv_file = open(file_path, 'r')
    try:
        count = 0
        for line in csv_file:
            # leave out first line
            if "zone name" in line.lower():
                continue
            health_facility, zone_name, zone_code = line.split(",")
            
            # make sure we find the right facility (everything but the 
            # last 2 digits is the facility code)
            facility_code = zone_code[:-3]
            try:
                facility = Location.objects.get(slug=facility_code)
            except Location.DoesNotExist:
                raise LoaderException("%s is not a valid facility code for zone %s" % (facility_code, zone_name))
            
            if facility.name != health_facility:
                print "WARNING: Expected facility %s but found %s for zone %s" % (health_facility, facility.name, zone_name) 
            
            try:
                zone = Location.objects.get(slug=zone_code)
            except Location.DoesNotExist:
                zone = Location(slug=zone_code)
            zone.name = zone_name
            zone.parent = facility
            zone.type = zone_type
            zone.save()
            count += 1
    
        if log_to_console: print "Successfully processed %s locations." % count
    
    finally:
        csv_file.close()
    
def _clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]