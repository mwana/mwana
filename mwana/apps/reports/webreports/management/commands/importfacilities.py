# vim: ai ts=4 sts=4 et sw=4
"""
assign facilities to a group by importing from another group
"""

from django.core.management.base import LabelCommand
from mwana.apps.locations.models import Location
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import ReportingGroup
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand



class Command(LabelCommand):
    help = ("Import facilities to one reporting group from another. Use only when sure of what you are doing")

    def handle(self, * args, ** options):

        if len(args) != 2:
            raise CommandError('Please specify 2 reporting groups')

        confirm = raw_input("Importing to %s from %s. Do you want to continue[Y/N]?" % (args[0], args[1]))
        if not confirm or confirm.lower() not in ["yes","y"]:
            print "quitted"
            return
        group1 = ReportingGroup.objects.get(name__iexact=args[0] )
        group2 = ReportingGroup.objects.get(name__iexact=args[1] )

        facilities = Location.objects.filter(groupfacilitymapping__group=group2)
        self.try_assign(group1, facilities)



    def try_assign(self, group, facilities):
        print "***" * 20
        print "%s has %s facilities" % (group.name, GroupFacilityMapping.objects.filter(group=group).count())

        for loc in facilities:
            GroupFacilityMapping.objects.get_or_create(group=group, facility=loc)
        print "%s now has %s facilities" % (group.name, GroupFacilityMapping.objects.filter(group=group).count())


    def __del__(self):
        pass
