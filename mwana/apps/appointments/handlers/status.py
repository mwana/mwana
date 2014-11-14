from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from .base import AppointmentHandler
from ..forms import StatusForm


class StatusHandler(AppointmentHandler):
    "Set the status of an appointment for the patient."

    keyword = 'status'
    form = StatusForm
    help_text = _('To set the status of the most recent appointment send: %(prefix)s %(keyword)s <KEY> <NAME/ID> <SAW|MISSED>')
    success_text = _('Thank you! The appointment status has been set.')

    def parse_message(self, text):
        "Tokenize message text."
        result = {}
        tokens = text.strip().split()
        result['keyword'] = tokens.pop(0)
        if tokens:
            # Next token is the name/id
            result['name'] = tokens.pop(0)
            if tokens:
                # Next token is the status
                result['status'] = ' '.join(tokens)
        return result
