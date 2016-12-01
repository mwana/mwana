# vim: ai ts=4 sts=4 et sw=4
""" Bootstrap StockAccounts
"""
import os

from django.core.management.base import LabelCommand, CommandError
from django.db.utils import IntegrityError
from mwana.apps.stockmini.models import Stock


class Command(LabelCommand):
    help = "Loads products from the specified csv file."
    args = "<file_path>"
    label = 'valid file path'

    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        file_path = (args[0])
        load_data(file_path)

    def __del__(self):
        pass


def load_data(file_path):
    if not os.path.exists(file_path):
        raise CommandError("Invalid file path: %s." % file_path)
    csv_file = open(file_path, 'r')

    count = 0
    for line in csv_file:
        code, name, pack_size = line.split("|")
        try:
            stock, created = Stock.objects.get_or_create(code=code, name=name, pack_size=pack_size)
            if created:
                count+=1
        except IntegrityError:
            print "Integrity error:", line

    print "created", count, "new records"
    csv_file.close()