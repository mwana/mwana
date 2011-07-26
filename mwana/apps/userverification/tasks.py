# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime
from datetime import timedelta
import logging

from mwana.apps.userverification.models import UserVerification
from mwana.const import get_clinic_worker_type
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact

logger = logging.getLogger(__name__)


VERICATION_MSG = "Hello %s. Are you still working at %s and still using Results160? Please respond with YES or No"

def send_verification_request(router):
    logger.info('sending verification request to clinic workers')

    days_back = 75
    today = datetime.today()
    date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)

    # TODO: leave out new clinic workers
    contacts = Contact.active.exclude(message__direction="I",
                                      message__date__gte=date_back).\
                                      filter(types=get_clinic_worker_type())
    
    counter = 0
    msg_limit = 9
    for contact in contacts:
        if UserVerification.objects.filter(contact=contact,
                                           facility=contact.location, request='1',
                                           verification_freq="A",
                                           request_date__gte=date_back).exists():
            continue

        msg = VERICATION_MSG % (contact.name, contact.location.name)

        OutgoingMessage(contact.default_connection, msg).send()

        UserVerification.objects.create(contact=contact,
                                        facility=contact.location, request='1', verification_freq="A")
        
        counter = counter + 1
        if counter >= msg_limit:
            break