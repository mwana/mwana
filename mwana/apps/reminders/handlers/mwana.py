# vim: ai ts=4 sts=4 et sw=4
import logging


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from ..forms import MwanaForm

logger = logging.getLogger(__name__)

MWANA_HELP = "To register a birth send: MWANA DATE M_FIRSTNAME M_LASTNAME C_FIRSTNAME C_LASTNAME"
UNREGISTERED = ""
TOO_FEW_TOKENS = ""
GARBLED_MSG = ""


class MwanaHandler(KeywordHandler):

    keyword = 'child'

    def help(self):
        """Respond with the MWANA help message"""
        self.respond(MWANA_HELP)

    def _get_tokens(self, text):
        """Splits the text into the expected fields"""
        tokens = text.split()
        if len(tokens) != 5:
            self.help()
        return {'date_of_birth': tokens[0],
                'mother_first_name': tokens[1],
                'mother_last_name': tokens[2],
                'child_first_name': tokens[3],
                'child_last_name': tokens[4]}

    def handle(self, text):

        from pudb import set_trace; set_trace()
        tokens = self._get_tokens(text)
        form = MwanaForm(tokens or None)
        if form.is_valid():
            # process
            date_of_birth = form.cleaned_data['date_of_birth']
            mother_first_name = form.cleaned_data['mother_first_name']
            mother_last_name = form.cleaned_data['mother_last_name']
            child_first_name = form.cleaned_data['child_first_name']
            child_last_name = form.cleaned_data['child_last_name']
            msg = "dob: %s, mf: %s, ml: %s, cf: %s, cl: %s"
            msg = msg % (date_of_birth, mother_first_name, mother_last_name,
                         child_first_name, child_last_name,)
            self.respond(msg)
        else:
            # return errors
            print form.errors
