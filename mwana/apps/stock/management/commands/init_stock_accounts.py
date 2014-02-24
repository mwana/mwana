# vim: ai ts=4 sts=4 et sw=4
""" Bootstrap StockAccounts
"""

from django.core.management.base import LabelCommand

from mwana.apps.locations.models import Location
from mwana.apps.stock.models import *

class Command(LabelCommand):
    help = """..."""


    def handle(self, * args, ** options):
        try:
            init_stock()
        except:
            #TODO
            pass
        init_stock_accounts()

def init_stock():
    Stock.objects.create(name='Doxycycline 100 mg tablet', code='DRG1-005');
    Stock.objects.create(name='Phenytoin Tablets', code='DRG1-010');
    Stock.objects.create(name='Any 1st line anti-malarial', code='DRG1-015');
    Stock.objects.create(name='Amoxicillin 125 mg / 5 ml suspension', code='DRG1-020');
    Stock.objects.create(name='Combined Oral contraceptive (ORALCON F)', code='DRG1-025');
    Stock.objects.create(name='Any 1st line ARV drug', code='DRG1-030');
    Stock.objects.create(name='4 FDC (TB) drug', code='DRG1-040');
    Stock.objects.create(name='Benzyl penicillin', code='DRG1-045');
    Stock.objects.create(name='Cotrimoxazole 480 mg', code='DRG1-050');
    Stock.objects.create(name='Oxytocin', code='DRG1-055');
    Stock.objects.create(name='DPT-HepB+Hib vaccine', code='DRG1-060');
    Stock.objects.create(name='ORS', code='DRG1-065');
    Stock.objects.create(name='Paracetamol 500 mg', code='DRG1-070');
    Stock.objects.create(name='Rapid HIV test', code='DRG1-075');
    Stock.objects.create(name='RPR test', code='DRG1-080');
    Stock.objects.create(name='RDT  test', code='DRG1-085');
    Stock.objects.create(name='Any 1st line STIs drug', code='DRG1-090');
    Stock.objects.create(name='Any Anti malaria for IPT', code='DRG1-095');

def init_stock_accounts():
    
    stocks = Stock.objects.all()

    locs = Location.objects.filter(supportedlocation__supported=True)

    for stock in stocks:
        for loc in locs:
            try:
                StockAccount.objects.create(stock=stock, location=loc);print ".",
            except:
                print "Error", stock, loc