# vim: ai ts=4 sts=4 et sw=4
from mwana.const import get_province_worker_type
from mwana.const import get_hub_worker_type
from mwana.const import get_district_worker_type
from mwana.const import get_cba_type
from django.db.models import Q
from mwana.apps.userverification.models import DeactivatedUser
from mwana.apps.userverification.messages import (PHO_VERICATION_MSG,
DHO_VERICATION_MSG, HUB_VERICATION_MSG, CBA_VERICATION_MSG, VERICATION_MSG)
from datetime import datetime
from datetime import timedelta
import logging

from mwana.apps.userverification.models import UserVerification
from mwana.const import get_clinic_worker_type
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact

logger = logging.getLogger(__name__)


def get_defaulters(days_back):
    today = datetime.today()
    date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)

    supported_contacts = Contact.active.filter(
                        Q(types__in=[get_clinic_worker_type(), get_cba_type(),
                        get_district_worker_type(), get_hub_worker_type(),
                        get_province_worker_type()]),
                        Q(location__supportedlocation__supported=True)|
                        Q(location__location__supportedlocation__supported=True)|
                        Q(location__location__location__supportedlocation__supported=True)|
                        Q(location__parent__supportedlocation__supported=True)
                        ).distinct()

    complying_contacts = supported_contacts.filter(message__direction="I", message__date__gte=date_back).distinct()


    return set(supported_contacts) - set(complying_contacts), date_back

def send_verification_request(router):
    logger.info('sending initial verification request to clinic workers')

    days_back = 75


    defaulting_contacts, date_back = get_defaulters(days_back)
    counter = 0
    msg_limit = 29

    logger.info('%s SMS contacts have not sent messages in the last %s days' % (len(defaulting_contacts), days_back))
        
    for contact in defaulting_contacts:
        if UserVerification.objects.filter(contact=contact,
                                           facility=contact.location, request='1',
                                           verification_freq="A",
                                           request_date__gte=date_back).exists():
            continue

        msg = VERICATION_MSG % (contact.name, contact.location.name)
        contact_types = contact.types.all()
        if get_cba_type() in contact_types:
            msg = CBA_VERICATION_MSG % (contact.name, contact.location.parent.name)
        elif get_hub_worker_type() in contact_types:
            msg = HUB_VERICATION_MSG % (contact.name, contact.location.name)
        elif get_district_worker_type() in contact_types:
            msg = DHO_VERICATION_MSG % (contact.name, contact.location.name)
        elif get_province_worker_type() in contact_types:
            msg = PHO_VERICATION_MSG % (contact.name, contact.location.name)

        OutgoingMessage(contact.default_connection, msg).send()

        UserVerification.objects.create(contact=contact,
                                        facility=contact.location, request='1', verification_freq="A")

        counter = counter + 1
        if counter >= msg_limit:
            break

def send_final_verification_request(router):
    #TODO Consider refactoring this method and above one into one
    logger.info('sending final verification request to SMS users')

    days_back = 120
    
    defaulting_contacts, date_back = get_defaulters(days_back)
    counter = 0
    msg_limit = 29

    for contact in defaulting_contacts:
        if UserVerification.objects.filter(contact=contact,
                                           facility=contact.location, request='2',
                                           verification_freq="F",
                                           request_date__gte=date_back).exists():
            continue

        msg = VERICATION_MSG % (contact.name, contact.location.name)
        contact_types = contact.types.all()
        if get_cba_type() in contact_types:
            msg = CBA_VERICATION_MSG % (contact.name, contact.location.parent.name)
        elif get_hub_worker_type() in contact_types:
            msg = HUB_VERICATION_MSG % (contact.name, contact.location.name)
        elif get_district_worker_type() in contact_types:
            msg = DHO_VERICATION_MSG % (contact.name, contact.location.name)
        elif get_province_worker_type() in contact_types:
            msg = PHO_VERICATION_MSG % (contact.name, contact.location.name)

        OutgoingMessage(contact.default_connection, msg).send()

        UserVerification.objects.create(contact=contact,
                                        facility=contact.location, request='2', verification_freq="F")

        counter = counter + 1
        if counter >= msg_limit:
            break

def inactivate_lost_users(router):
    logger.debug('in inactivate_lost_users')

    days_back = 127
    today = datetime.today()
    date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)


    supported_contacts = Contact.active.filter(
                        Q(types__in=[get_clinic_worker_type(), get_cba_type(),
                        get_district_worker_type(), get_hub_worker_type(),
                        get_province_worker_type()]),
                        Q(location__supportedlocation__supported=True)|
                        Q(location__location__supportedlocation__supported=True)|
                        Q(location__location__location__supportedlocation__supported=True)|
                        Q(location__parent__supportedlocation__supported=True)
                        ).distinct()
    
    warned_contacts = supported_contacts.filter(userverification__request=2).distinct()

    complying_contacts = supported_contacts.filter(message__direction="I", message__date__gte=date_back).distinct()



    defaulting_contacts = set(warned_contacts) - set(complying_contacts)


    for contact in defaulting_contacts:
        contact.is_active = False
        contact.save()
        conn = contact.default_connection
        conn.contact = None
        conn.save()        

        DeactivatedUser(contact=contact, connection=conn).save()
