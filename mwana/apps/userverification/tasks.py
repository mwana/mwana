# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.userverification.models import DeactivatedUser
from mwana.apps.userverification.messages import VERICATION_MSG
from datetime import datetime
from datetime import timedelta
import logging

from mwana.apps.userverification.models import UserVerification
from mwana.const import get_clinic_worker_type
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
from rapidsms.models import Connection

logger = logging.getLogger(__name__)



def send_verification_request(router):
    logger.info('sending verification request to clinic workers')

    days_back = 75
    today = datetime.today()
    date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)


    supported_contacts = Contact.active.filter(types=get_clinic_worker_type(),
    location__supportedlocation__supported=True).distinct()

    complying_contacts = supported_contacts.filter(message__direction="I", message__date__gte=date_back).distinct()



    defaulting_contacts = set(supported_contacts) - set(complying_contacts)
    counter = 0
    msg_limit = 19

    logger.info('%s clinic workers have not sent messages in the last %s days' % (len(defaulting_contacts), days_back))
    
    
    for contact in defaulting_contacts:
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

def send_final_verification_request(router):
    #TODO Consider refactoring this method and above one into one
    logger.info('sending 6 month verification request to clinic workers')

    days_back = 120
    today = datetime.today()
    date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)


    supported_contacts = Contact.active.filter(types=get_clinic_worker_type(),
    location__supportedlocation__supported=True).distinct()

    complying_contacts = supported_contacts.filter(message__direction="I", message__date__gte=date_back).distinct()



    defaulting_contacts = set(supported_contacts) - set(complying_contacts)
    counter = 0
    msg_limit = 19

    logger.info('%s clinic workers have not sent messages in the last %s days' % (len(defaulting_contacts), days_back))


    for contact in defaulting_contacts:
        if UserVerification.objects.filter(contact=contact,
                                           facility=contact.location, request='2',
                                           verification_freq="F",
                                           request_date__gte=date_back).exists():
            continue

        msg = VERICATION_MSG % (contact.name, contact.location.name)

        OutgoingMessage(contact.default_connection, msg).send()

        UserVerification.objects.create(contact=contact,
                                        facility=contact.location, request='2', verification_freq="F")

        counter = counter + 1
        if counter >= msg_limit:
            break

def inactivate_lost_users(router):

    days_back = 127
    today = datetime.today()
    date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)


    supported_contacts = Contact.active.filter(types=get_clinic_worker_type(),
    location__supportedlocation__supported=True).distinct()

    complying_contacts = supported_contacts.filter(message__direction="I", message__date__gte=date_back).distinct()



    defaulting_contacts = set(supported_contacts) - set(complying_contacts)

    
    for contact in defaulting_contacts:
        contact.is_active = False
        contact.save()
        conn = None
        try:
            conn= Connection.objects.get(contact=contact)
            conn.contact = None
            conn.save()
        except Connection.DoesNotExist:
            pass

        DeactivatedUser(contact=contact, connection=conn).save()