# vim: ai ts=4 sts=4 et sw=4
"""

"""

from django.core.management.base import LabelCommand

from mwana.apps.anc.messages import EDUCATIONAL_MESSAGES
from mwana.apps.anc.models import EducationalMessage


class Command(LabelCommand):
    help = "Populate ANC Messages"
    args = ""
    
    def handle(self, * args, ** options):
        process()
                
    def __del__(self):
        pass


def process():
    for item in EDUCATIONAL_MESSAGES:
        EducationalMessage.objects.get_or_create(gestational_age=item[0], text=item[1])
