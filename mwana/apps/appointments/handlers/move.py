from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from .base import AppointmentHandler
from ..forms import MoveForm


class MoveHandler(AppointmentHandler):
    "Reschdule the next appointment for the patient."

    keyword = 'move'
    form = MoveForm
    help_text = _('To reschedule the next appointment send: %(prefix)s %(keyword)s <KEY> <NAME/ID> <DATE>')
    success_text = _('Thank you! The appointment has been rescheduled.')

    def parse_message(self, text):
        "Tokenize message text."
        result = {}
        tokens = text.strip().split()
        result['keyword'] = tokens.pop(0)
        if tokens:
            # Next token is the name/id
            result['name'] = tokens.pop(0)
            if tokens:
                # Remaining tokens should be a date string
                result['date'] = ' '.join(tokens)
        return result
