# vim: ai ts=4 sts=4 et sw=4


from mwana.const import get_clinic_worker_type
from mwana.const import get_cba_type
from rapidsms.models import Contact
from mwana.apps.reports.models import Coverage
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from django.core.management.base import LabelCommand
from django.db.utils import IntegrityError
import re
from django.core.management.base import CommandError

class Command(LabelCommand):
    help = "Create MGIC Coverage data"
    label = 'valid file path'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Please specify a %s' % self.label)
        update_sites(args[0])
        

def __del__(self):
    pass

def update_sites(path):
    file = open(path, 'r')
    location_type = LocationType.objects.get(singular='Health Centre')
    for line in file:
        district_given, facility_given = (s.strip() for s in line.split(','))
        a = Coverage()

        coverage, created = Coverage.objects.get_or_create(raw_district_text=district_given, raw_facility_text=facility_given)

        # @type coverage Coverage
        if not coverage.location:
            if '8' in coverage.raw_facility_text and not coverage.matched:
                slug = re.findall(r'8\d+', coverage.raw_facility_text)[0][:6]
                locs = Location.objects.filter(slug=slug)
                if locs:
                    try:
                        loc = locs[0]
                        coverage.location = loc
                        coverage.supported = loc.supportedlocation_set.filter(supported=True).exists()
                        coverage.number_of_active_staff = Contact.active.filter(location=loc, types=get_clinic_worker_type()).count()
                        coverage.number_of_active_cba = Contact.active.filter(location__parent=loc, types=get_cba_type()).count()
                        coverage.matched = True
                        coverage.save()
                    except IntegrityError, e:
                        print "django.db.utils.IntegrityError", e, facility_given, "in", district_given, 'against'
                else:
                    try:
                        Location.objects.create(slug=slug, name=facility_given,
                        parent=Location.objects.get(name=district_given, type__slug='districts'), type=location_type)
                    except Location.DoesNotExist:
                        print "creating new facility failed for district", district_given
                    


            elif not coverage.matched:
                print 'processing', district_given, facility_given
                try:
                    loc = Location.objects.filter(parent__name=district_given).filter(name=facility_given)
                    if not loc:
                        loc = Location.objects.filter(parent__parent__name='Southern').get(name=facility_given)
                    else:
                        loc = loc[0]
                    print loc.slug, loc.name, loc.id
                    coverage.location = loc
                    coverage.supported = loc.supportedlocation_set.filter(supported=True).exists()
                    coverage.number_of_active_staff = Contact.active.filter(location=loc, types=get_clinic_worker_type()).count()
                    coverage.number_of_active_cba = Contact.active.filter(location__parent=loc, types=get_cba_type()).count()
                    coverage.matched = True
                    coverage.save()
                except Location.DoesNotExist:
                    print facility_given, "in", district_given, 'not found in Mwana'
                except Location.MultipleObjectsReturned:
                    print "MultipleObjectsReturned for", facility_given, "in", district_given
                except IntegrityError, e:
                    print "django.db.utils.IntegrityError", e, facility_given, "in", district_given, 'against'

                
