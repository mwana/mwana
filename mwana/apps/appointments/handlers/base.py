from __future__ import unicode_literals

import re

from django.utils.translation import ugettext_lazy as _

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class AppointmentHandler(KeywordHandler):
    "Base keyword handler for the APPT prefix."

    prefix = 'APPT'
    form = None
    success_text = ''

    @classmethod
    def _keyword(cls):
        if hasattr(cls, "keyword"):
            pattern = r"^\s*(?:%s)\s*(?:%s)(?:[\s,;:]+(.+))?$" % (cls.prefix, cls.keyword)
        else:
            pattern = r"^\s*(?:%s)\s*?$" % cls.prefix
        return re.compile(pattern, re.IGNORECASE)

    def handle(self, text):
        "Parse text, validate data, and respond."
        parsed = self.parse_message(text)
        form = self.form(data=parsed, connection=self.msg.connection)
        if form.is_valid():
            params = form.save()
            self.respond(self.success_text % params)
        else:
            error = form.error()
            if error is None:
                self.unknown()
            else:
                self.respond(error)
        return True

    def help(self):
        "Return help mesage."
        if self.help_text:
            keyword = self.keyword.split('|')[0].upper()
            help_text = self.help_text % {'prefix': self.prefix, 'keyword': keyword}
            self.respond(help_text)

    def unknown(self):
        "Common fallback for unknown errors."
        keyword = self.keyword.split('|')[0].upper()
        params = {'prefix': self.prefix, 'keyword': keyword}
        self.respond(_('Sorry, we cannot understand that message. '
            'For additional help send: %(prefix)s %(keyword)s') % params)
