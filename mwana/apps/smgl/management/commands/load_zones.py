from django.core.management.base import BaseCommand
import os
from ... import loader 

class Command(BaseCommand):
    help = "load zones from a csv file."

    def handle(self, *args, **options):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fixtures", "kalomo_district_zones.csv")
        print path
        loader.load_zones(path, log_to_console=True)