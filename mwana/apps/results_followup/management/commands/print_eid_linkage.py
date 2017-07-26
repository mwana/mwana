# vim: ai ts=4 sts=4 et sw=4
"""

"""
import logging
from datetime import date, datetime

from django.core.management.base import LabelCommand

from mwana.apps.results_followup.models import InfantResultAlert

logger = logging.getLogger('mwana.apps.results_followup.create_followup_results')


class Command(LabelCommand):
    help = "Populate/update InfantResultAlert data"
    args = ""
    
    def handle(self, * args, ** options):
        process(args)
                
    def __del__(self):
        pass


def clean(item):
    if item:
        if isinstance(item, date) or isinstance(item, datetime):
            return str(item)[:10]
        return str(item)
    return ''


def process(args=['SMACHT']):
    print 'followup_status,created_on,location,referred_to,birthdate,sex,verified,collected_on,processed_on,date_retrieved,treatment_start_date'
    for r in InfantResultAlert.objects.filter(location__groupfacilitymapping__group__name__in=args):
        print ','.join(clean(x) for x in [r.followup_status, r.created_on, r.location, r.referred_to,
                                          r.birthdate, r.sex, r.verified, r.collected_on, r.processed_on,
                                          r.date_retrieved, r.treatment_start_date])
