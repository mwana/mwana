from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from .base import AppointmentHandler
from ..forms import QuitForm


class QuitHandler(AppointmentHandler):
    "Unsubscribes a user to a timeline."

    keyword = 'quit'
    form = QuitForm
    success_text = _('Thank you%(user)s! You unsubcribed from the %(timeline)s for '
        '%(name)s on %(date)s. You will be no longer be notified when it is time for the next appointment.')
    help_text = _('To unsubcribe a user from a timeline send: %(prefix)s %(keyword)s <KEY> <NAME/ID> <DATE>. '
        'The date is optional.')

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
