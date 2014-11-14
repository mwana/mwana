from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from rapidsms.router import send

from appointments.handlers.base import AppointmentHandler
from ..forms import CollectForm


class CollectHandler(AppointmentHandler):

    "Notifies a client that results are ready for collection."
    prefix = ''
    keyword = 'collect'
    form = CollectForm
    success_text = _('Thank you %(user)s! We have notified the carer at'
                     ' %(phoneid)s the result %(id)s is available for '
                     'collection.')
    client_text = _('Hello, Please note your result is ready for '
                    'collection at the clinic.')
    help_text = _('To notify a client that results are available send: '
                  '%(keyword)s <NAME/ID>')
    unregistered = _('You are not registered as a mobile agent. Please'
                     'send JOIN for information on how to register.')

    def parse_message(self, text):
        "Tokenize message text."
        result = {}
        tokens = text.strip().split()
        result['keyword'] = "collect"
        if tokens:
            # Next token is the sample id
            result['sample_id'] = tokens.pop(0)
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
        if form.is_valid():
            params = form.save()
            self.respond(self.success_text % params)
            if params['phone'] is not None:
                send(self.client_text, params['phone'])
        else:
            error = form.error()
            if error is None:
                self.unknown()
            else:
                self.respond(error)
        return True
