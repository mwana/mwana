# vim: ai ts=4 sts=4 et sw=4
"""
Import Incidents from a given pipe separated file with the following fields:
Incident name, [Type (default=dis)], [Abbr], [Indicator_id]
"""

from mwana.apps.surveillance.models import Alias
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from mwana.apps.surveillance.models import Incident
import os


class Command(LabelCommand):
    help = ("Import Incidents from a given pipe separated file")

    def handle(self, * args, ** options):

        if len(args) != 1:
            raise CommandError('Please specify one file path')

        file_path = args[0]
        if not os.path.exists(file_path):
            raise CommandError("Invalid file path: %s." % file_path)

        self.load_diseases(file_path)

    def load_diseases(self, path):
        file = open(path, 'r')

        count = 0
        count_old = 0
        count_tt = 0
        alias_count = Alias.objects.count()
        for line in file:
            count_tt += 1
            tokens = line.strip().split('|')
            #allow different number of columns in inout file
            name = tokens[0].strip() or None
            type = "".join(tokens[1:2]) or None
            abbr = "".join(tokens[2:3]) or None
            indicator_id = "".join(tokens[3:4]) or None

            incident = Incident()
            try:
                incident = Incident.objects.get(name__iexact=name)
                count_old += 1
            except Incident.DoesNotExist:
                incident.name = name
                if type: incident.type = type
                if abbr: incident.abbr = abbr
                if indicator_id: incident.indicator_id = indicator_id

                incident.save()
                count += 1

        print ("Added %s incidents from %s specified in file. %s already exist."
        " Created %s aliases" % (count, count_tt, count_old, Alias.objects.count() - alias_count))

    def __del__(self):
        pass
