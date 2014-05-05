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

    def handle(self, text):
        child = text.strip()
        try:
            patient = Person.objects.get(code=child)
            ass = patient.latest_assessment()
            if ass is not None:
                ass.cancel()
                self.respond(CANCEL_CONFIRM %
                             (ass.healthworker.name,
                              ass.healthworker.interviewer_id,
                              ass.date, patient.code))
            else:
                self.respond(CANCEL_ERROR % (child,))
        except ObjectDoesNotExist:
            self.respond(CANCEL_ERROR % (child,))
