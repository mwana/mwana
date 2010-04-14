""" This script downloads synchronization data from a remote server,
deletes local xforms and submissions, and loads the data

"""

from django.core.management.base import LabelCommand, CommandError
import random

class Command(LabelCommand):
    help = "Creates somewhat realistic locations in Zambia in handy JSON format for loading into a db"
    args = "<number_of_locations>"
    label = 'Number of locations'
    
    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        num_locations = int(args[0])
        create_locations(num_locations)
                
    def __del__(self):
        pass
    
def create_locations(count):
    # give django some time to bootstrap itself
    from rapidsms.contrib.locations.models import LocationType, Location, Point
    health_center_type = LocationType.objects.get_or_create\
        (singular="health facility", plural="health facilities",
         slug="health_facilities")[0]
    
    for i in range(count):
        lat, lon = _zambian_coordinate()
        point = Point.objects.create(latitude=str(lat), longitude=str(lon))
        name = _new_facility_name()
        Location.objects.create(name=name,point=point,
                                type=health_center_type,
                                slug=name[:30])
    print "Successfully created %s new locations" % count

def _new_facility_name():
    from rapidsms.contrib.locations.models import Location
    name = "%s %s" % (random.choice(PLACES_IN_ZAMBIA), 
                      random.choice(HEALTH_CENTER_TYPES))
    try:
        Location.objects.get(name=name)
        return _new_facility_name()
    except Location.DoesNotExist:
        return name
    
def _zambian_coordinate():
    # a rough way to get a lat/lon in zambia.
    min_lat = -16.83609
    max_lat = -9.335252
    min_lon = 22.5
    max_lon = 32.827148
    lat = random.uniform(min_lat, max_lat)
    lon = random.uniform(min_lon, max_lon)
    if _out_of_bounds(lat, lon):
        return _zambian_coordinate()
    return (lat,lon)

def _out_of_bounds(lat, lon):
    # we use this to snip off areas of the map where the country
    # cuts in.  this is super rough
    return (lat < -14.44 and lon > 30.640869) or \
           (lat > -13.63531 and lon < 29.838867)
            
HEALTH_CENTER_TYPES = \
["Clinic", "Rural Health Center", "Hospital"]
# List of places taken from: http://en.wikipedia.org/wiki/List_of_cities_and_towns_in_Zambia
PLACES_IN_ZAMBIA = \
["Lusaka", "Ndola", "Kitwe", "Kabwe", "Chingola", "Mufulira", "Livingstone", "Luanshya",
 "Kasama", "Chipata", "Chililabombwe", "Solwezi", "Chadiza", "Chama", "Chambeshi", "Chavuma",
 "Chembe", "Chibombo", "Chiengi", "Chilubi", "Chinsali", "Chinyingi", "Chirundu", "Chisamba",
 "Choma", "Gwembe", "Isoka", "Kabompo", "Kafue", "Kafulwe", "Kalabo", "Kalomo", "Kalulushi",
 "Kanyembo", "Kaoma", "Kapiri Mposhi", "Kasempa", "Kashikishi", "Kataba", "Katete", "Kawambwa",
 "Kazembe", "Kazungula", "Luangwa", "Lufwanyama", "Lukulu", "Lundazi", "Macha Mission", "Makeni",
 "Mansa", "Mazabuka", "Mbala", "Mbereshi", "Mfuwe", "Milenge", "Misisi", "Mkushi", "Mongu",
 "Monze", "Mpika", "Mporokoso", "Mpulungu", "Mumbwa", "Muyombe", "Mwinilunga", "Nchelenge",
 "Ngoma", "Nkana", "Nseluka", "Pemba", "Petauke", "Samfya", "Senanga", "Serenje", "Sesheke",
 "Shiwa Ngandu", "Siavonga", "Sikalongo", "Sinazongwe", "Zambezi", "Zimba"
]
