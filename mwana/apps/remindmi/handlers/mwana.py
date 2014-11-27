from __future__ import unicode_literals
import string

from django.utils.translation import ugettext_lazy as _

from appointments.handlers.new import NewHandler

from ..forms import MwanaForm


class MwanaHandler(NewHandler):
    prefix = ''
    keyword = 'mwana'
    form = MwanaForm

    success_text = _('Thank you%(user)s! You registered a birth for '
                     '%(name)s on %(date)s. You will be notified when'
                     ' it is time for the next appointment.')
    help_text = _('To register a birth: %(keyword)s <DATE_OF_BIRTH> '
                  '<MOTHERSFIRSTNAME_MOTHERSLASTNAME/ID> '
                  '<CHILDFIRSTNAME_CHILDLASTNAME/ID>. ')
    unregistered = _('You need to be registered to report a birth.'
                     ' Send JOIN for more information.')

    def is_phone(text):
        return all(ch in set(string.digits) for ch in text)

    def parse_message(self, text):
        "Tokenize message text."
        result = {'keyword': 'mwana'}
        tokens = [t.upper() for t in text.strip().split()]
        # check length of tokens and process accordingly
        if len(tokens) == 5 and not self.is_phone(tokens[4]):
            result['date'] = tokens[0]
            result['mother_name'] = '_'.join(tokens[1:3])
            result['child_name'] = '_'.join(tokens[3:])
            result['volunteer'] = ''
        elif len(tokens) == 6 and self.is_phone(tokens[5]):
            result['date'] = tokens[0]
            result['mother_name'] = '_'.join(tokens[1:3])
            result['child_name'] = '_'.join(tokens[3:5])
            result['volunteer'] = tokens[5]
        elif len(tokens) == 3:
            result['date'] = tokens[0]
            result['mother_name'] = tokens[1]
            result['child_name'] = tokens[2]
            result['volunteer'] = ''
        elif len(tokens) == 4 and self.is_phone(tokens[3]):
            result['date'] = tokens[0]
            result['mother_name'] = tokens[1]
            result['child_name'] = tokens[2]
            result['volunteer'] = tokens[3]
        # result['location'] = self.msg.connection.contact.location
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
