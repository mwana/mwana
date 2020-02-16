# vim: ai ts=4 sts=4 et sw=4
'''
Created on Apr 12, 2011

@author: Trevor Sinkala
'''

from mwana.const import get_phia_worker_type
import logging

from mwana.apps.labresults.messages import *
from mwana.apps.labresults.models import Result
from mwana.const import get_cba_type
from mwana.const import get_clinic_worker_type
from mwana.const import get_district_worker_type
from mwana.const import get_hub_worker_type
from mwana.const import get_province_worker_type
from mwana.apps.labresults.messages import BAD_PIN
from mwana.apps.labresults.messages import CLINIC_DEFAULT_RESPONSE
from mwana.apps.labresults.messages import HUB_DEFAULT_RESPONSE
from mwana.apps.labresults.messages import CBA_DEFAULT_RESPONSE
from mwana.apps.labresults.messages import DHO_DEFAULT_RESPONSE
from mwana.apps.labresults.messages import PHO_DEFAULT_RESPONSE
from mwana.apps.labresults.messages import UNREGISTERED_DEFAULT_RESPONSE
import rapidsms

logger = logging.getLogger(__name__)


class App (rapidsms.apps.base.AppBase):
    """
    Responds with error messages relevant to the user
    """

    def handle (self, message):
        text = message.text.strip()
        contact = message.contact
        if not contact:
            message.respond(UNREGISTERED_DEFAULT_RESPONSE)
            return True
        if hasattr(message, "possible_bad_pin"):
            message.respond(BAD_PIN)
            return True
        if hasattr(message, "possible_bad_mock_pin"):
            message.respond(BAD_PIN)
            return True

        # Clinic worker: pin issues
        if is_pin(text) and ready_results(contact).count() == 0 and get_clinic_worker_type() in contact.types.all():
            message.respond("Hello %s. Are you trying to retrieve new "
                            "results? There are no new results ready for you. We shall let "
                            "you know as soon as they are ready." % contact.name)
            return True

        if is_pin(text) and notified_results(contact).count() > 0 and get_clinic_worker_type() in contact.types.all():
            if is_pin_correct(text, message):
                message.respond("Sorry %s. If you are trying "
                                "to retrieve new results please send the keyword CHECK." % contact.name)
            else:
                message.respond("Hello %s. If you are trying to retrieve new "
                                "results please send the keyword CHECK. Make sure you send your"
                                " correct PIN when asked to." % contact.name)
                
            return True    
        elif is_pin(text) and fresh_results(contact).count() > 0 and get_clinic_worker_type() in contact.types.all():
            if is_pin_correct(text, message):
                message.respond("Hello %s. If you are trying to retrieve new "
                                "results please send the keyword CHECK." % contact.name)
            else:
                message.respond("Hello %s. If you are trying to retrieve new "
                                "results please send the keyword CHECK. Make sure you send your"
                                " correct PIN when asked to." % contact.name)

            return True        

        # CBAs
        for key in ['remind me', 'remind mi', 'to remind me', 'to remind mi', 'remindme', 'remindmi', 'to remindme', 'to remindmi']:
            if text.lower().startswith(key):
                message.respond("Sorry %s, we didn't understand that message. "
                                "Send the keyword HELP if you need to be helped." % contact.name)
                return True


        skip_words = ["yes", "no", "thanks", "thank you"]
        for word in skip_words:
            if text.lower() == word or text.lower().startswith('%s ' % word):
                return True

        if get_clinic_worker_type() in contact.types.all():
            message.respond(CLINIC_DEFAULT_RESPONSE)
        elif get_cba_type() in contact.types.all():
            message.respond(CBA_DEFAULT_RESPONSE)
        elif get_district_worker_type() in contact.types.all():
            message.respond(DHO_DEFAULT_RESPONSE)
        elif get_hub_worker_type() in contact.types.all():
            message.respond(HUB_DEFAULT_RESPONSE)
        elif get_province_worker_type() in contact.types.all():
            message.respond(PHO_DEFAULT_RESPONSE % contact.name)
            message.respond(HUB_DEFAULT_RESPONSE)
        elif get_phia_worker_type() in contact.types.all():
            message.respond(PHO_DEFAULT_RESPONSE % contact.name)
            
        return True


def is_pin(text):
    return len(text) == 4 and text.isdigit()

def is_pin_correct(text, message):
    return message.contact.pin and message.contact.pin == text

def ready_results(contact):
    return Result.objects.filter(clinic__contact=contact,
                                 notification_status__in=['new', 'notified'])
def notified_results(contact):
    return Result.objects.filter(clinic__contact=contact,
                                 notification_status__in=['notified'])
def fresh_results(contact):
    return Result.objects.filter(clinic__contact=contact,
                                 notification_status__in=['new'])