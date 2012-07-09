#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.conf import settings
from rapidsms.apps.base import AppBase
from rapidsms.models import Contact
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.default.models import DefaultResponse
import logging

logging = logging.getLogger(__name__)
class App(AppBase):
    def handle(self, msg):
        logging.error('In Default Response App Handler')
        ident = msg.connection.identity
        try:
            contact = Contact.objects.get(connection__identity=ident)
            lang = contact.language
            if not lang:
                lang = "EN"
            msgs = DefaultResponse.objects.filter(language=lang)
            if msgs.count() > 0:
                msg.error(msgs[0])
            else:
                raise ObjectDoesNotExist("We couldn't find a defaut response message for the language specified: %s" % lang)
        except ObjectDoesNotExist:
            logging.error("We couldn't find a defaut response message for message: %s" % msg)
            if settings.DEFAULT_RESPONSE is not None:
                msg.error(settings.DEFAULT_RESPONSE,
                    project_name=settings.PROJECT_NAME)

