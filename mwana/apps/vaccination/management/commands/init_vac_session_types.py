# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.vaccination.models import VaccinationSession
from django.core.management.base import LabelCommand

import logging

logger = logging.getLogger(__name__)
class Command(LabelCommand):
    help = ("")

    def handle(self, * args, ** options):
        self.load_data()


    def __del__(self):
        pass

    def load_data(self):
         s1 = VaccinationSession.objects.get_or_create(session_id='s1', predecessor=None, min_child_age=0)[0]#BCG
         s2 = VaccinationSession.objects.get_or_create(session_id='s2', predecessor=None, min_child_age=0, max_child_age=13)[0]#OPV0
         s3 = VaccinationSession.objects.get_or_create(session_id='s3', predecessor=None, min_child_age=6 * 7)[0]#OPV1, etc
         s4 = VaccinationSession.objects.get_or_create(session_id='s4', predecessor=s3, min_child_age=4 * 7)[0]#OPV2, etc
         s5 = VaccinationSession.objects.get_or_create(session_id='s5', predecessor=s4, min_child_age=4 * 7)[0]#OPV3, etc
         s6 = VaccinationSession.objects.get_or_create(session_id='s6', predecessor=None, min_child_age=548)[0]#measles at 18 months
         s7 = VaccinationSession.objects.get_or_create(session_id='s7', predecessor=None, given_if_not_exist='s2', min_child_age=274)[0]#At 9 months, only if OPV0 was not given

         print "VaccinationSession now has", VaccinationSession.objects.count(), "records\n", "\n".join(o.__unicode__() for o in VaccinationSession.objects.all()[:7])

