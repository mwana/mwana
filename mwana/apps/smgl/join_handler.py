import logging

from rapidsms.models import Contact
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.smgl.models import PreRegistration
from mwana.apps.smgl.app import _send_msg, _get_value_for_command,NOT_PREREGISTERED, get_location, \
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
        _send_msg(connection, NOT_PREREGISTERED, router)
        return True

    if prereg.has_confirmed:
        contact = Contact.objects.get(connection__identity__icontains=prereg.phone_number)
        session.template_vars.update({
            "name": contact.name,
            "readable_user_type": contact.types.all()[0].name,
            "facility": contact.location.name
        })
        _send_msg(session.connection, ALREADY_REGISTERED, router, **session.template_vars)
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

    #Create a contact for this connection.  If it already exists,
    #Verify that it is a contact of the specified type. If not,
    #Add it.  If it does already have that type associated with it
    # Return a message indicating that it is already registered.
    #Same logic for facility.
    connection = session.connection
    reg_type = prereg.title.lower()
    facility = prereg.facility_code
    fname = prereg.first_name #these provided in pre-reg info
    lname = prereg.last_name
    name = _get_value_for_command('name', xform) #this provided by user
    zone_name = prereg.zone
    uid = prereg.unique_id
    language = (_get_value_for_command('language', xform) or prereg.language).lower()

    session.template_vars.update({
        'reg_type': reg_type,
        'facility': facility,
        'first_name': fname,
        'last_name': lname,
        'name': name,
        'zone': zone_name,
        'unique_id': uid
    })

    logger.debug('Data from Pre Registration and Input XForm:: Facility: %s, Registration type: %s, Connection: %s, Name:%s, UID:%s' % \
                 (facility, reg_type, connection, '%s %s' % (fname, lname), uid))

    location, error = get_location(session, facility)
    if error:
        _send_msg(connection, FACILITY_NOT_RECOGNIZED, router, **session.template_vars)
        return True
    contactType, error = get_contacttype(session, reg_type)
    session.template_vars.update({"title": reg_type, "facility": location.name})
    if error:
        _send_msg(connection, CONTACT_TYPE_NOT_RECOGNIZED, router, **session.template_vars)
        return True
    #update the template dict to have a human readable name of the type of contact we're registering
    session.template_vars.update({"readable_user_type": contactType.name})

    zone = None
    if zone_name and reg_type == 'cba':
        zone, error = _get_or_create_zone(location, zone_name)
    elif zone_name and reg_type != 'cba':
        logger.debug('Zone field was specified even though registering type is not CBA')
        _send_msg(connection, ZONE_SPECIFIED_BUT_NOT_CBA, router, **session.template_vars)
        return True

    #UID constraints (like isnum and length) should be caught by the rapidsms_xforms constraint settings for the form.
    #Name can't really be validated.

    contact_name = '%s %s' % (fname, lname)
    if name: #we prefer to use the user provided name in all communications. Lname and Fname saved in preRegistration data
        contact_name = name
    contact, created = Contact.objects.get_or_create(name = contact_name,
                                                location=(zone or location),
                                                unique_id = uid,
                                                language=language[:5]
    )
    session.connection.contact = contact
    session.connection.save()
    types = contact.types.all()
    if contactType not in types:
        contact.types.add(contactType)
    else: #Already registered
        logger.debug('HERE ARE THE TEMPLATE_VARS: %s' % session.template_vars)
        _send_msg(connection, ALREADY_REGISTERED, router, **session.template_vars)
        return True
    contact.location = location
    contact.save()

    #lastly, link this contact to its owning pre-reg info
    prereg.contact = contact
    prereg.has_confirmed = True
    prereg.save()
    _send_msg(connection, USER_SUCCESS_REGISTERED, router, **session.template_vars)
    return True

