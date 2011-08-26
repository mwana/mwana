# vim: ai ts=4 sts=4 et sw=4
import re
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from mwana.apps.nutrition.messages import *
from mwana.apps.nutrition.models import *


class RegisterHandler(KeywordHandler):

    keyword = "register|reg"

    def help(self):
        self.respond(REGISTER_HELP)

    def __register_healthworker(self, interviewer_id, name, lang="eng-us"):
        self.debug('registering healthworker...')
        try:
            # find healthworker via interviewer_id and add new connection
            # (e.g., registering from a second connection)
            alias, first, last = Contact.parse_name(name)
            healthworker = Contact.objects.get(interviewer_id=interviewer_id,\
                first_name=first, last_name=last, name=name)
            self.msg.connection.contact=healthworker
            self.msg.connection.save()
            return healthworker, False
        except ObjectDoesNotExist, MultipleObjectsReturned:
            try:
                # TODO remove connection from previous hw
                # parse the name, and create a healthworker/reporter
                # (e.g., registering from first connection)
                alias, first, last = Contact.parse_name(name)
                healthworker = Contact(
                    first_name=first, last_name=last, alias=alias,
                    interviewer_id=interviewer_id, language=lang, name=name)
                healthworker.save()
                self.msg.connection.contact=healthworker
                self.msg.connection.save()
                return healthworker, True
            # something went wrong - at the
            # moment, we don't care what
            except Exception, e:
                self.exception('problem registering worker')

    def handle(self, text):
        # handle the text
        #parse using re instead of logic.
        p = re.compile(r'(?P<code>\d+)\s+(?P<name>\D*)',
                       re.IGNORECASE)
        try:
            m = p.search(text)
            code = m.group('code')
            name = m.group('name').strip()
        except ValueError:
            self.respond("There is an error in your submission \
                         please check the format and try again.")

        self.debug("register...")
        try:
            healthworker, created = self.__register_healthworker(code, name)
            if created:
                self.respond(REGISTER_CONFIRM % (healthworker.name, healthworker.interviewer_id))
            else:
                self.respond(REGISTER_AGAIN % (healthworker.name))
        except Exception, e:
            self.exception("oops! problem registering healthworker")
            self.respond("An Exception occured, the health worker was not created.")
            