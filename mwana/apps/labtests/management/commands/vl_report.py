# vim: ai ts=4 sts=4 et sw=4

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand

from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.labtests.models import Result


class Command(LabelCommand):
    help = "Outputs a report for viral load results."
    args = "<Reporting Group>"
    label = 'valid Mwana Reporting Group such SMACHT'
    
    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        process(args[0])
                
    def __del__(self):
        pass


def process(name):
    groups = ReportingGroup.objects.filter(name__iexact=name.strip())
    if not groups:
        print("Reporting Group with name %s does not exist" % name)
        return
    group = groups[0]


    results = Result.objects.filter(clinic__groupfacilitymapping__group=group)

    locations = set(res.clinic for res in results)
    print "Location|Code|Sent|Pending"
    for loc in locations:
        print("|".join(str(x) for x in [loc.name, loc.slug, results.filter(notification_status='sent', clinic=loc).count(), results.filter(clinic=loc, notification_status__in=['new', 'updated', 'notified']).count()]))

