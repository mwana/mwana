from rapidsms.models import Contact
from threadless_router.router import Router
from app import _get_value_for_command
from django.core.exceptions import ObjectDoesNotExist
from models import PreRegistration
import logging
from mwana.apps.smgl.app import _send_msg, NOT_PREREGISTERED, get_location, FACILITY_NOT_RECOGNIZED, get_contacttype, CONTACT_TYPE_NOT_RECOGNIZED, _get_or_create_zone, ZONE_SPECIFIED_BUT_NOT_CBA, ALREADY_REGISTERED, USER_SUCCESS_REGISTERED


router = Router()

logger = logging.getLogger(__name__)
def join_secure(session, xform):
    connection = session.connection
    try:
        prereg = PreRegistration.objects.get(phone_number=connection.identity)
    except ObjectDoesNotExist:
        _send_msg(connection, NOT_PREREGISTERED)
        return True

    if prereg.has_confirmed:
        _send_msg(session.connection, ALREADY_REGISTERED)
        return True
    else:
        return join_generic(session, xform, prereg)



def join_generic(session, xform, prereg):
    """
    This is the generic JOIN handler for the SMGL project.
    It deals with registering CBA's, Triage Nurses, Ambulance Drivers
    and Hospital Staff

    Message Format:
    JOIN UniqueID NAME FACILITY TITLE(TN/DA/CBA) ZONE(IF COUNSELLOR)
    """
    logger.debug('Handling the JOIN keyword form')

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
    language = prereg.language
    session.template_vars.update({
        'reg_type': reg_type,
        'facility': facility,
        'first_name': fname,
        'last_name': lname,
        'name': name,
        'zone': zone_name,
        'unique_id': uid
    })


    logger.debug('Facility: %s, Registration type: %s, Connection: %s, Name:%s, UID:%s' % \
                 (facility, reg_type, connection, '%s %s' % (fname, lname), uid))

    location, error = get_location(session, facility)
    if error:
        _send_msg(connection, FACILITY_NOT_RECOGNIZED, **session.template_vars)
        return True
    contactType, error = get_contacttype(session, reg_type)
    session.template_vars.update({"title": reg_type})
    if error:
        _send_msg(connection, CONTACT_TYPE_NOT_RECOGNIZED, **session.template_vars)
        return True
    #update the template dict to have a human readable name of the type of contact we're registering
    session.template_vars.update({"readable_user_type": contactType.name})

    zone = None
    if zone_name and reg_type == 'cba':
        zone = _get_or_create_zone(location, zone_name)
    elif zone_name and reg_type != 'cba':
        logger.debug('Zone field was specified even though registering type is not CBA')
        _send_msg(connection, ZONE_SPECIFIED_BUT_NOT_CBA, **session.template_vars)
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
        _send_msg(connection, ALREADY_REGISTERED, **session.template_vars)
        return True
    contact.location = location
    contact.save()

    #lastly, link this contact to its owning pre-reg info
    prereg.contact = contact
    prereg.has_confirmed = True
    prereg.save()
    _send_msg(connection, USER_SUCCESS_REGISTERED, **session.template_vars)
    return True

