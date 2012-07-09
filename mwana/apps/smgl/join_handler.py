import logging

from rapidsms.models import Contact
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.smgl.models import PreRegistration
from mwana.apps.smgl.app import send_msg, get_value_from_form,NOT_PREREGISTERED, \
    FACILITY_NOT_RECOGNIZED, get_contacttype, CONTACT_TYPE_NOT_RECOGNIZED, _get_or_create_zone, \
    ZONE_SPECIFIED_BUT_NOT_CBA, ALREADY_REGISTERED, USER_SUCCESS_REGISTERED

logger = logging.getLogger(__name__)
# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s


def join_secure(session, xform, router):
    logger.debug('HANDLING JOIN KEYWORD')
    logger.debug('Router: %s.  Instance of: %s' % (router, type(router)))
    connection = session.connection
    try:
        prereg = PreRegistration.objects.get(phone_number=connection.identity)
    except ObjectDoesNotExist:
        logger.debug('Could not find a PreRegistration Object corresponding to the identity:%s' % connection.identity)
        logger.debug('Prereg objects are: %s' % PreRegistration.objects.all())
        send_msg(connection, NOT_PREREGISTERED, router)
        return True

    if prereg.has_confirmed:
        contact = Contact.objects.get(connection__identity__icontains=prereg.phone_number)
        language = get_value_from_form('language', xform) 
        if language:
            contact.language = language
            contact.save()
        send_msg(session.connection, ALREADY_REGISTERED, router, **{
            "name": contact.name,
            "readable_user_type": contact.types.all()[0].name,
            "facility": contact.location.name
        })
        return True
    else:
        return join_generic(session, xform, prereg, router)



def join_generic(session, xform, prereg, router):
    """
    This is the generic JOIN handler for the SMGL project.
    It deals with registering CBA's, Triage Nurses, Ambulance Drivers
    and Hospital Staff

    Message Format:
    JOIN UniqueID NAME FACILITY TITLE(TN/DA/CBA) ZONE(IF COUNSELLOR)
    """

    # Create a contact for this connection.  If it already exists,
    # Verify that it is a contact of the specified type. If not,
    # Add it.  If it does already have that type associated with it
    # Return a message indicating that it is already registered.
    # Same logic for facility.
    connection = session.connection
    reg_type = prereg.title.lower()
    fname = prereg.first_name #these provided in pre-reg info
    lname = prereg.last_name
    name = get_value_from_form('name', xform) #this provided by user
    zone_name = prereg.zone
    uid = prereg.unique_id
    language = (get_value_from_form('language', xform) or prereg.language).lower()

    if not prereg.location:
        send_msg(connection, FACILITY_NOT_RECOGNIZED, router, **{'facility': prereg.location})
        return True
    
    contactType = get_contacttype(reg_type)
    if not contactType:
        send_msg(connection, CONTACT_TYPE_NOT_RECOGNIZED, router, 
                 **{"title": reg_type})
        return True
    
    zone = None
    if zone_name and reg_type == 'cba':
        zone, error = _get_or_create_zone(prereg.location, zone_name)
    elif zone_name and reg_type != 'cba':
        logger.debug('Zone field was specified even though registering type is not CBA')
        send_msg(connection, ZONE_SPECIFIED_BUT_NOT_CBA, router, **{'reg_type': reg_type})
        return True

    # UID constraints (like isnum and length) should be caught by the 
    # rapidsms_xforms constraint settings for the form.
    # Name can't really be validated.

    contact_name = '%s %s' % (fname, lname)
    if name: 
        # we prefer to use the user provided name in all communications. 
        # Lname and Fname saved in preRegistration data
        contact_name = name
    contact, created = Contact.objects.get_or_create(name=contact_name,
                                                     location=(zone or prereg.location),
                                                     unique_id=uid,
                                                     language=language[:5])
    session.connection.contact = contact
    session.connection.save()
    types = contact.types.all()
    if contactType not in types:
        contact.types.add(contactType)
    else: #Already registered
        send_msg(connection, ALREADY_REGISTERED, router, **{"readable_user_type": contactType.name,
                                                            'name': name,
                                                            'facility': prereg.location})
        return True
    contact.location = prereg.location
    contact.save()

    #lastly, link this contact to its owning pre-reg info
    prereg.contact = contact
    prereg.has_confirmed = True
    prereg.save()
    send_msg(connection, USER_SUCCESS_REGISTERED, router, **{"readable_user_type": contactType.name,
                                                             'facility': prereg.location})
    return True

