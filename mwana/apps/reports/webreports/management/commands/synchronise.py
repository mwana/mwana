# vim: ai ts=4 sts=4 et sw=4
"""
for each facility assigned to a group check if it also assigened to "MoH HQ"
and "SUPPORT" groups, if not then assign.
"""

from django.core.management.base import LabelCommand
from mwana.apps.locations.models import Location
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import ReportingGroup



class Command(LabelCommand):
    help = ("Synchronise group facilities with Support and MoH HQ Groups."
            "For each facility assigned to a group check if it also assigened to MoH HQ"
            "and SUPPORT groups, if not then assign.")

    def handle(self, * args, ** options):

        facilities = Location.objects.exclude(groupfacilitymapping__group=None)

        moh = suport = None
        support_name = "support"
        moh_name = "moh"
        try:
            moh = ReportingGroup.objects.get(id=1, name__icontains=moh_name)
            suport = ReportingGroup.objects.get(id=2, name__icontains=support_name)
        except:
            pass
        if moh and facilities:
            self.try_assign(moh, facilities)
        else:
            print "%s might have changed" % moh_name

        if suport and facilities:
            self.try_assign(suport, facilities)
        else:
            print "%s might have changed" % support_name



    def try_assign(self, group, facilities):
        print "***" * 20
        print "%s has %s facilities" % (group.name, GroupFacilityMapping.objects.filter(group=group).count())

        for loc in facilities:
            GroupFacilityMapping.objects.get_or_create(group=group, facility=loc)
        print "%s now has %s facilities" % (group.name, GroupFacilityMapping.objects.filter(group=group).count())


    def __del__(self):
        pass
