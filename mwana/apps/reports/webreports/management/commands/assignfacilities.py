# vim: ai ts=4 sts=4 et sw=4
"""
assign facilities to a group
"""

from django.core.management.base import LabelCommand
from mwana.apps.locations.models import Location
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import ReportingGroup
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand



class Command(LabelCommand):
    help = ("assign facilities to reporing group\nUsage: assignfacilities DISTRICT_CODE")

    def handle(self, * args, ** options):


        if len(args) < 1:
            raise CommandError('Please specify district slug.')

        slug = args[0]

        district = Location.objects.get(slug=slug)
        district_name = district.name
        print "District is %s"%district.name
        print "Province is %s"%district.parent.name
        dho= ReportingGroup.objects.get_or_create(name="DHO %s" %district_name )[0]
        pho = ReportingGroup.objects.get_or_create(name="PHO %s" %district.parent.name.split()[0] )[0]

        

        facilities = Location.objects.filter(parent=district, send_live_results=True, supportedlocation__supported=True)
        self.try_assign(dho, facilities)
        self.try_assign(pho, facilities)
       


    def try_assign(self, group, facilities):
        print "***" * 20
        print "%s has %s facilities" % (group.name, GroupFacilityMapping.objects.filter(group=group).count())

        for loc in facilities:
            GroupFacilityMapping.objects.get_or_create(group=group, facility=loc)
        print "%s now has %s facilities" % (group.name, GroupFacilityMapping.objects.filter(group=group).count())


    def __del__(self):
        pass
