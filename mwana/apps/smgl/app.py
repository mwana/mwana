from mwana.apps.agents.handlers.agent import get_unique_value
from mwana.apps.locations.models import Location, LocationType
from rapidsms.models import Contact
from mwana.apps.contactsplus.models import ContactType
from rapidsms_xforms.models import xform_received, XForm
from .models import XFormKeywordHandler
from rapidsms.messages import OutgoingMessage
import logging
from django.core.exceptions import ObjectDoesNotExist
from mwana import const

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

# Begin Translatable messages
FACILITY_NOT_RECOGNIZED = _("Sorry, the facility '%(fac)s' is not recognized. Please try again.")
ALREADY_REGISTERED = _("%(name)s, you are already registered as a %(readable_user_type)s at %(fac)s but your details have been updated")
CONTACT_TYPE_NOT_RECOGNIZED = _("Sorry, the Title Code '%(title)s' is not recognized. Please try again.")
ZONE_SPECIFIED_BUT_NOT_CBA = _("You can not specify a zone when registering as a %(reg_type)s!")
USER_SUCCESS_REGISTERED =  _("Thank you for registering! You have successfully registered as a %(readable_user_type)s at %(fac)s.")

logger = logging.getLogger('mwana.apps.smgl.app')
logger.setLevel(logging.DEBUG)

def _get_standard_xform_response(submission, xform):
    """
    Gets the template rendered response as normally returned by rapidsms_xforms
    """
    return XForm.render_response(xform.response, submission.template_vars)

def _get_value_for_command(command, submission):
    try:
        return submission.values.get(attribute__xformfield__command=command).value
    except ObjectDoesNotExist:
        return None

def _get_valid_model(model,slug=None,name=None):
    if not slug and not name:
        logger.debug('No location name or slug specified while attempting to get valid model for %s' % model)
        return None
    try:
        if slug:
            return model.objects.get(slug=slug.lower)
        else:
            return model.objects.get(name=name)
    except ObjectDoesNotExist:
        return None

 # Taken from mwana.apps.agents.handler.agrent.AgentHandler
def _get_or_create_zone(clinic, name):
    # create the zone if it doesn't already exist
    zone_type, _ = LocationType.objects.get_or_create(slug=const.ZONE_SLUGS[0])
    zone = Location.objects.get_or_create(name__iexact=name,
                                parent=clinic,
                                type=zone_type,
                                defaults={
                                    'name': name,
                                    'slug': get_unique_value(Location.objects, "slug", name),
                                })

###############################################################################
##              BEGIN RAPIDSMS_XFORMS KEYWORD HANDLERS                       ##
##===========================================================================##
def join_generic(submission, xform):
    """
    This is the generic JOIN handler for the SMGL project.
    It deals with registering CBA's, Triage Nurses, Ambulance Drivers
    and Hospital Staff

    """
    logger.debug('Handling the JOIN keyword form')

    #Create a contact for this connection.  If it already exists,
    #Verify that it is a contact of the specified type. If not,
    #Add it.  If it does already have that type associated with it
    # Return a message indicating that it is already registered.
    #Same logic for facility.
    connection = submission.connection
    reg_type = _get_value_for_command('title', submission).lower()
    facility = _get_value_for_command('fac', submission)
    name = _get_value_for_command('name', submission)
    zone_name = _get_value_for_command('zone', submission)
    uid = _get_value_for_command('uid', submission)

    logger.debug('Facility: %s, Registration type: %s, Connection: %s, Name:%s, UID:%s' % \
                 (facility, reg_type, connection, name, uid))

    location = _get_valid_model(Location, name=facility)
    if not location:
        logger.debug('A valid location was not found for %s' % facility)
        OutgoingMessage(connection, FACILITY_NOT_RECOGNIZED, **submission.template_vars).send()
        return True
    logger.debug('Got a valid location')
    contactType = _get_valid_model(ContactType, slug=reg_type)
    if not contactType:
        OutgoingMessage(connection, CONTACT_TYPE_NOT_RECOGNIZED, **submission.template_vars).send()
        return True
    logger.debug('Got a good ContactType')
    #update the template dict to have a human readable name of the type of contact we're registering
    submission.template_vars.update({"readable_user_type": contactType.name})

    zone = None
    if zone_name and reg_type == 'cba':
        zone = _get_or_create_zone(location, zone_name)
    elif zone_name and reg_type != 'cba':
        logger.debug('Zone field was specified even though registering type is not CBA')
        OutgoingMessage(connection, ZONE_SPECIFIED_BUT_NOT_CBA, **submission.template_vars)
        return True

    #UID constraints (like isnum and length) should be caught by the rapidsms_xforms constraint settings for the form.
    #Name can't really be validated.

    (contact, created) = Contact.objects.get_or_create(name=name, location=(zone or location), alias = uid)
    submission.connection.contact = contact
    submission.connection.save()
    types = contact.types.all()
    if contactType not in types:
        contact.types.add(contactType)
    else: #Already registered
        OutgoingMessage(connection, ALREADY_REGISTERED, **submission.template_vars).send()
        return True
    contact.location = location
    contact.save()

    OutgoingMessage(connection, USER_SUCCESS_REGISTERED, **submission.template_vars).send()

    #prevent default response
    return True


def pregnant_registration(submission, xform):
    pass

def follow_up_appt(submission, xform):
    pass

def ambulance_request(submission, xform):
    pass

def ambulance_driver_response(submission, xform):
    pass

def referral(submission, xform):
    pass

def birth_registration(submission, xform):
    """
    Keyword: BIRTH
    """
    print 'Got the xform and submission for the BIRTH Keyword!!'
    print 'Submission: %s' % submission
    print 'Xform: %s' % xform
    logging.debug('-================================++!!!!!!!!!!!!!!!!!!!!+===========-')

def death_registration(submission, xform, **args):
    pass
###############################################################################

def get_handler_func(funcpath):
    dot = funcpath.rindex('.')
    module = funcpath[:dot]
    func_name = funcpath[(dot+1):]
    module = __import__(module, fromlist=[func_name]) #one would think that this returns the function. One would be wrong (???).
                                                      #it returns the module only.  Without the fromlist param it imports the project root __init__.py (???)
    return getattr(module, func_name)  #this does return the function.



# define a listener
def handle_submission(sender, **args):
    submission = args['submission']
    xform = args['xform']
    keyword = xform.keyword
    has_errors = submission.has_errors

    if has_errors:
        logger.debug('Attempted to handle form submission with keyword: %s but the form had errors.' % keyword)
        return
    try:
        kw_handler = XFormKeywordHandler.objects.get(keyword=keyword)
    except ObjectDoesNotExist:
        logger.debug('No keyword handler found for the xform submission with keyword: %s' % keyword)
        return

    func = get_handler_func(kw_handler.function_path)

    #call the actual handling function
    return func(submission, xform)

# then wire it to the xform_received signal
xform_received.connect(handle_submission)