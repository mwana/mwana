import datetime
import logging

from .models import XFormKeywordHandler, FacilityVisit

from mwana.apps.agents.handlers.agent import get_unique_value
from mwana.apps.locations.models import Location, LocationType
from mwana.apps.contactsplus.models import ContactType
from mwana.apps.smgl.models import PregnantMother
from mwana import const

from rapidsms_xforms.models import xform_received, XForm
from rapidsms.models import Contact
from rapidsms.messages import OutgoingMessage

from dimagi.utils.modules import to_function

from django.core.exceptions import ObjectDoesNotExist


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
MOTHER_SUCCESS_REGISTERED = _("Thank you, mother has been registered succesfully!")
NOT_REGISTERED_FOR_DATA_ASSOC = _("Sorry, this number is not registered. Please register with the JOIN keyword and try again")
NOT_A_DATA_ASSOCIATE = _("You are not registered as a Data Associate and are not allowed to register mothers!")
DATE_INCORRECTLY_FORMATTED_GENERAL = _("The date you entered for %(date_name)s is incorrectly formatted.  Format should be "
                                       "DD MM YYYY. Please try again.")

DATE_YEAR_INCORRECTLY_FORMATTED = _("The year you entered for date %(date_name)s is incorrectly formatted.  Should be in the format"
                                    "YYYY (four digit year). Please try again.")

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

def get_location(submission, facility):
    location = _get_valid_model(Location, name=facility)
    error = False
    if not location:
        logger.debug('A valid location was not found for %s' % facility)
        OutgoingMessage(submission.connection, FACILITY_NOT_RECOGNIZED, **submission.template_vars).send()
        error = True
    return location, error


def get_contacttype(submission, reg_type):
    contactType = _get_valid_model(ContactType, slug=reg_type)
    error = False
    if not contactType:
        OutgoingMessage(submission.connection, CONTACT_TYPE_NOT_RECOGNIZED, **submission.template_vars).send()
        error=True
    return contactType, error

###############################################################################
##              BEGIN RAPIDSMS_XFORMS KEYWORD HANDLERS                       ##
##===========================================================================##
def join_generic(submission, xform):
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
    connection = submission.connection
    reg_type = _get_value_for_command('title', submission).lower()
    facility = _get_value_for_command('fac', submission)
    name = _get_value_for_command('name', submission)
    zone_name = _get_value_for_command('zone', submission)
    uid = _get_value_for_command('uid', submission)

    logger.debug('Facility: %s, Registration type: %s, Connection: %s, Name:%s, UID:%s' % \
                 (facility, reg_type, connection, name, uid))

    location, error = get_location(submission, facility)
    if error:
        return True
    contactType, error = get_contacttype(submission, reg_type)
    if error:
        return True
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

    (contact, created) = Contact.objects.get_or_create(name=name, location=(zone or location), unique_id = uid)
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

def _make_date(dd, mm, yy):
    """
    Returns a tuple: (datetime.date, ERROR_MSG)
    ERROR_MSG will be False if datetime.date is sucesfully constructed.
    Be sure to include the dictionary key-value "date_name": DATE_NAME
    when sending out the error message as an outgoing message.
    """
    try:
        dd = int(dd)
        mm = int(mm)
        yy = int(yy)
    except ValueError:
        return None, DATE_INCORRECTLY_FORMATTED_GENERAL

    if yy < 1900: #Make sure yy is a 4 digit date
        return None, True, DATE_YEAR_INCORRECTLY_FORMATTED

    try:
        ret_date = datetime.date(yy,mm,dd)
    except ValueError as msg:
        return None, True, msg #<-- will send descriptive message of exact error (like month not in 1..12, etc)

    return ret_date, False, None



def pregnant_registration(submission, xform):
    """
    Handler for REG keyword (registration of pregnant mothers).
    Format:
    REG Mother_UID FIRST_NAME LAST_NAME HIGH_RISK_HISTORY FOLLOW_UP_DATE_dd FOLLOW_UP_DATE_mm FOLLOW_UP_DATE_yyyy \
        REASON_FOR_VISIT(ROUTINE/NON-ROUTINE) ZONE LMP_dd LMP_mm LMP_yyyy EDD_dd EDD_mm EDD_yyyy
    """
    logger.debug('Handling the REG keyword form')

    #Create a contact for this connection.  If it already exists,
    #Verify that it is a contact of the specified type. If not,
    #Add it.  If it does already have that type associated with it
    # Return a message indicating that it is already registered.
    #Same logic for facility.
    connection = submission.connection

    #get or create a new Mother Object without saving the object (and triggering premature errors)
    uid = _get_value_for_command('uid', submission)
    try:
        mother = PregnantMother.objects.get(uid=uid)
    except ObjectDoesNotExist:
        mother = {}

    mother["name"] = _get_value_for_command('first_name', submission)
    mother["uid"] = uid
    mother["high_risk_history"] = _get_value_for_command('high_risk_history', submission)
    mother["next_visit"] = _get_value_for_command('next_visit', submission)
    mother["reason_for_visit"] = _get_value_for_command('reason_for_visit', submission)
    zone_name = _get_value_for_command('zone', submission)
    date_name = {"date_name": "LMP"}

    lmp_dd = _get_value_for_command('lmp_dd', submission)
    lmp_mm = _get_value_for_command('lmp_mm', submission)
    lmp_yy = _get_value_for_command('lmp_yy', submission)

    lmp_date, error, error_msg = _make_date(lmp_dd, lmp_mm, lmp_yy)
    if error:
        OutgoingMessage(connection, error_msg, **date_name)

    mother["lmp"] = lmp_date



    logger.debug('Mother UID: %s, is_referral: %s' % \
                 (mother.uid, str(mother.is_referral)))

    #We must get the location from the Contact (Data Associate) who should be registered with this
    #phone number.  If the contact does not exist (unregistered) we throw an error.
    contactType, error = get_contacttype(submission, 'da') #da = Data Associate
    if error:
        OutgoingMessage(connection, NOT_A_DATA_ASSOCIATE)
        return True
    logging.debug('Data associate:: Connection: %s, Type: %s' % (connection, contactType))
    try:
        data_associate = Contact.objects.get(connection=connection, types=contactType)
    except ObjectDoesNotExist:
        logger.info("Data Associate Contact not found.  Mother cannot be correctly registered!")
        OutgoingMessage(connection, NOT_REGISTERED_FOR_DATA_ASSOC)
        return True

    mother.location = data_associate.location
    if zone_name:
        mother.zone = _get_or_create_zone(mother.location, zone_name)
    mother.save()

    #Create a facility visit object and link it to the mother
    visit = FacilityVisit()
    visit.location = mother.location
    visit.visit_date = datetime.date.today()
    visit.reason_for_visit = 'initial_registration'
    visit.next_visit = mother.next_visit
    visit.mother = mother
    visit.save()

    OutgoingMessage(connection, MOTHER_SUCCESS_REGISTERED, **submission.template_vars).send()
    #prevent default response
    return True

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
    func = to_function(kw_handler.function_path, True)
    #call the actual handling function
    return func(submission, xform)

# then wire it to the xform_received signal
xform_received.connect(handle_submission)