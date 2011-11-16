# vim: ai ts=4 sts=4 et sw=4
import re
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.nutrition.messages import *
from mwana.apps.nutrition.models import *

class RemoveHandler(KeywordHandler):
    """
    Remove a specified Health Interviewer.
    """

    keyword = "deregister|dereg"


    def help(self):
        self.respond(REMOVE_HELP)


    def handle(self, text):
        p = re.compile(r'(?P<code>\d+)\D*', re.IGNORECASE)
        try:
            m = p.match(text)
            code = m.group('code')
        except Exception, e:
            self.respond(INVALID_MESSAGE)
            self.exception()

        try:
            healthworker = Contact.objects.get(interviewer_id=code)
            healthworker.status = 'I'
            healthworker.save()
            self.respond(REMOVE_CONFIRM %
                        (healthworker.name, healthworker.interviewer_id))
            healthworker.interviewer_id = None 
            healthworker.save()
        except Exception, e:
            self.respond(INVALID_MESSAGE)
            self.exception()
