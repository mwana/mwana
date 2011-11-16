# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.nutrition.messages import *


class DismissHandler(KeywordHandler):
    """
    Discharge a child from a nutrition programme.
    """

    keyword = "dismiss|dis"

    def help(self):
        self.respond(DISMISS_HELP)


    def handle(self, text):
        pass
