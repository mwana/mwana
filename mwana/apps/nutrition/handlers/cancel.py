# vim: ai ts=4 sts=4 et sw=4
import re
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.nutrition.messages import *
from mwana.apps.nutrition.models import *

from people.models import PersonType


class CancelHandler(KeywordHandler):
    """
    Cancel the last reported assessment.
    """

    keyword = "cancel|can"

    def help(self):
        self.respond(CANCEL_HELP)

    def __identify_healthworker(self):
        # return the healthworker if already registered on this connection
        try:
            if self.msg.connections[0].contact is not None:
                healthworker = self.msg.connections[0].contact
                return healthworker
            else:
                return None
        except ObjectDoesNotExist:
            return None

    def __latest_assessment(self, patient, healthworker):
        assessments = Assessment.objects.exclude(status='C').filter(
            patient=patient,
            healthworker=healthworker).order_by('-date')
        if len(assessments) > 0:
            return assessments[0]
        else:
            return None

    def handle(self, text):
        child = text.strip()
        healthworker = self.__identify_healthworker()
        if healthworker is None:
            return self.respond(
                "Please register as a Mobile Agent before using AnthroWatch.")
        location = healthworker.clinic.slug
        try:
            patient = Person.objects.get(code=child, cluster_id=location)
            ass = self.__latest_assessment(patient, healthworker)
            if ass is not None:
                ass.cancel()
                self.respond(CANCEL_CONFIRM %
                             (ass.healthworker.name,
                              ass.date, patient.code))
            else:
                self.respond(CANCEL_ERROR % (child,))
        except ObjectDoesNotExist:
            self.respond(CANCEL_ERROR % (child,))
