from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from rapidsms.router import send

from mwana.apps.appointments.handlers.new import NewHandler
from ..forms import MayiForm
from ..tasks import generate_appointments


class MayiHandler(NewHandler):
    prefix = ''
    keyword = 'mayi'
    form = MayiForm

    success_text = _('Thank you%(user)s! You registered a pregnancy for '
                     '%(name)s at %(location_name)s on %(date)s. You '
                     'will be notified when it is time for the next '
                     'appointment.')
    help_text = _('To register a mother: %(keyword)s <EDD:YYYY-MM-DD>'
                  '<MOTHERS_PATIENT_ID> '
                  '<DOB:YYYY-MM-DD> <MOTHERS_PHONE|X> <STATUS:P|N|U>. ')
    unregistered = _('Please register before registering a mother. Send '
                     'JOIN for more information.')

    def parse_message(self, text):
        "Tokenize message text."
        # TODO: support old form without dob
        result = {'keyword': 'mayi'}
        tokens = [t.upper() for t in text.strip().split()]
        # check # of tokens and deal with old version
        if len(tokens) == 6:
            result['edd'] = tokens[0]
            result['firstname'] = tokens[1]
            result['lastname'] = tokens[2]
            result['dob'] = tokens[3]
            result['name'] = "_".join(tokens[1:3])
            result['phone'] = tokens[4]
            result['status'] = tokens[5]
        elif len(tokens) == 5:
            result['edd'] = tokens[0]
            result['name'] = tokens[1]
            result['dob'] = tokens[2]
            result['phone'] = tokens[3]
            result['status'] = tokens[4]
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
            return True
        parsed = self.parse_message(text)
        form = self.form(data=parsed, connection=self.msg.connection)
        if form.is_valid():
            params = form.save()
            self.respond(self.success_text % params)
            if params['mother_registered'] is not None:
                msg = _('%(name)s, you have been subscribed to receive '
                        'reminders by %(user)s. Please let them know if'
                        'you want to stop.') % params
                send(msg, [params['patient_conn']])
            elif params['mother_registered'] is None and params['patient_conn'] is not None:
                msg = _('%(user)s, the phone number for the mother is already '
                        'registered to someone in the system, only you '
                        'will receive her reminders.') % params
                self.respond(msg)
            generate_appointments(days=365)
        else:
            error = form.error()
            if error is None:
                self.unknown()
            else:
                self.respond(error)
        return True
