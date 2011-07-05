# vim: ai ts=4 sts=4 et sw=4
from rapidsms.contrib.handlers import KeywordHandler

from mwana.apps.nutrition.messages import *


class RemoveHandler(KeywordHandler):
    """
    Remove a specified Health Interviewer.
    """

    keyword = "remove|rem"


    def help(self):
        self.respond(REMOVE_HELP)


    def handle(self, text):
# fix this
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

