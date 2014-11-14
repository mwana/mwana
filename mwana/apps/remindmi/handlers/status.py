from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from appointments.handlers.base import AppointmentHandler
from ..forms import StatusForm


class StatusHandler(AppointmentHandler):
    "Set the status of an appointment for the patient."
    prefix = ''
    keyword = 'status'
    form = StatusForm
    help_text = _('To set the status of the most recent appointment send:'
                  ' %(prefix)s %(keyword)s <NAME|ID> <FOUND|REFUSED|'
                  'LOST|MOVED|DEAD>')
    success_text = _('Thank you! The appointment status has been set.')

    def parse_message(self, text):
        "Tokenize message text."
        result = {}
        tokens = text.strip().split()
        result['keyword'] = tokens[0]
        # Next token is the name/id
        result['name'] = tokens[1].upper()
        # Next token is the status
        result['status'] = tokens[2]
        return result
