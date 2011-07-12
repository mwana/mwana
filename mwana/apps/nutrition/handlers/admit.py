# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import re
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.nutrition.messages import *


class AdmitHandler(KeywordHandler):
    """
    Admit a child to a nutrition program.
    """

    keyword = "admit|adm"

    def help(self):
        self.respond(ADMIT_HELP)

    def handle(self, text):
        #parse using re instead of logic.
        p = re.compile(r'(?P<child_id>\d{5})(?P<child_name>\D+)',
                       re.IGNORECASE)
        try:
            m = p.search(text)
            child_id = m.group('child_id')
            child_name = m.group('child_name').strip()
        except ValueError:
            self.respond("There is an error in your submission \
                         please check the format and try again.")

        self.respond("You sent the following details: ChildID: %s, Name: %s."
                     % (child_id, child_name))
