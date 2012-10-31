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
    help = ("assign facilities ro reporing group\nUsage: assignfacilities DISTRICT_NAME")

    def handle(self, * args, ** options):


        if len(args) < 2:
            raise CommandError('Please specify district followed by slug.')

        district_name = args[0]
        slug = args[1]

        district = Location.objects.get(name__iexact=district_name, slug=slug)

        print "Province is %s"%district.parent.name
        dho = ReportingGroup.objects.get(name__iexact="DHO %s" %district_name )
        pho = ReportingGroup.objects.get(name__iexact="PHO %s" %district.parent.name.split()[0] )

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
