from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from mwana.apps.appointments.handlers.base import AppointmentHandler
from ..forms import RefillForm


class RefillHandler(AppointmentHandler):
    "Create an ART refill appointment for the patient."
    prefix = ''
    keyword = 'refill'
    form = RefillForm
    help_text = _('To create a refill appointment send:'
                  ' %(prefix)s %(keyword)s <NAME|ID> <DATE>')
    success_text = _('Thank you! The appointment for %(name)s '
                     ' has been created on %(date)s.')

    def parse_message(self, text):
        "Tokenize message text."
        result = {}
        tokens = text.strip().split()
        result['keyword'] = tokens.pop(0)
        if tokens:
            # Next token is the name
            result['name'] = tokens.pop(0)
            if tokens:
                # Next token is the date
                result['date'] = tokens.pop(0)
        return result

    def check_healthworker(self):
        if self.msg.connection.contact is not None:
            self.healthworker = self.msg.connection.contact
            if self.healthworker.location is not None:
                self.location = self.healthworker.location
            else:
                self.location = None
            return self.healthworker, self.location
        else:
            self.healthworker = None
            self.location = None
            return None, None

    def handle(self, text):
        "Check reporter, parse text, validate data, and respond."
        healthworker, location = self.check_healthworker()
        if healthworker is None or location is None:
            self.respond(self.unregistered)
        parsed = self.parse_message(text)
        form = self.form(data=parsed, connection=self.msg.connection)
        if form. is_valid():
            params = form.save()
            self.respond(self.success_text % params)
        else:
            error = form.error()
            if error is None:
                self.unknown()
            else:
                self.respond(error)
        return True
