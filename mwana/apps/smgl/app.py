import datetime
import logging
from rapidsms.apps.base import AppBase

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
from threadless_router.router import Router

from django.core.exceptions import ObjectDoesNotExist
from smscouchforms.signals import xform_saved_with_session

from smsforms.signals import form_complete


# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

router = Router()

# Begin Translatable messages
FACILITY_NOT_RECOGNIZED = _("Sorry, the facility '%(facility)s' is not recognized. Please try again.")
ALREADY_REGISTERED = _("%(name)s, you are already registered as a %(readable_user_type)s at %(facility)s but your details have been updated")
CONTACT_TYPE_NOT_RECOGNIZED = _("Sorry, the Title Code '%(title)s' is not recognized. Please try again.")
ZONE_SPECIFIED_BUT_NOT_CBA = _("You can not specify a zone when registering as a %(reg_type)s!")
USER_SUCCESS_REGISTERED =  _("Thank you for registering! You have successfully registered as a %(readable_user_type)s at %(facility)s.")
MOTHER_SUCCESS_REGISTERED = _("Thank you, mother has been registered succesfully!")
NOT_REGISTERED_FOR_DATA_ASSOC = _("Sorry, this number is not registered. Please register with the JOIN keyword and try again")
NOT_A_DATA_ASSOCIATE = _("You are not registered as a Data Associate and are not allowed to register mothers!")
DATE_INCORRECTLY_FORMATTED_GENERAL = _("The date you entered for %(date_name)s is incorrectly formatted.  Format should be "
                                       "DD MM YYYY. Please try again.")

DATE_YEAR_INCORRECTLY_FORMATTED = _("The year you entered for date %(date_name)s is incorrectly formatted.  Should be in the format"
                                    "YYYY (four digit year). Please try again.")

NOT_PREREGISTERED = _('Sorry, you are not on the pre-registered users list. Please contact ZCAHRD for assistance')

DATE_ERROR = _('%(error_msg)s for %(date_name)s')

logger = logging.getLogger(__name__)

class SMGL(AppBase):
    #overriding because seeing router|mixin is so unhelpful it makes me want to throw my pc out the window.
    @property
    def _logger(self):
        return logging.getLogger(__name__)
    def handle(self, msg):
        pass

    # We're handling the submission process using signal hooks
    # Code is located here (in app.py) for ease of finding for other devs.

def _send_msg(connection, txt, **kwargs):
    logger.debug('Connection: %s, txt: %s, kwargs: %s' % (connection, txt, kwargs))
    omsg = OutgoingMessage(connection, txt, **kwargs)
    router.outgoing(omsg)

def _get_value_for_command(command, xform):
    try:
        return xform.xpath('form/%s' % command)
    except ObjectDoesNotExist:
        return None

def _get_valid_model(model,slug=None,name=None, iexact=False):
    if not slug and not name:
        logger.debug('No location name or slug specified while attempting to get valid model for %s' % model)
        return None
    try:
        if slug:
            if not iexact:
                return model.objects.get(slug=slug)
            else:
                return model.objects.get(slug__iexact=slug)
        else:
            if not iexact:
                return model.objects.get(name=name)
            else:
                return model.objects.get(name__iexact=name)
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



def get_location(session, facility):
    logger.debug('In get_location(), Session: %s, Facility: %s' % (session, facility))
    location = _get_valid_model(Location, name=facility, iexact=True)
    error = False
    if not location:
        logger.debug('A valid location was not found for %s' % facility)
        error = True
    return location, error

def get_contacttype(session, reg_type):
    contactType = _get_valid_model(ContactType, slug=reg_type, iexact=True)
    error = False
    if not contactType:
        error=True
    return contactType, error

def _make_date(dd, mm, yy):
    """
    Returns a tuple: (datetime.date, ERROR_MSG)
    ERROR_MSG will be False if datetime.date is sucesfully constructed.
    Be sure to include the dictionary key-value "date_name": DATE_NAME
    when sending out the error message as an outgoing message.
    """
    logger.debug('in _make_date(). Trying to make a date from %s %s %s' % (dd,mm,yy))
    try:
        dd = int(dd)
        mm = int(mm)
        yy = int(yy)
    except ValueError as ve:
        logger.debug('In Make Date: ve %s' % ve)
        return None, True, DATE_INCORRECTLY_FORMATTED_GENERAL

    if yy < 1900: #Make sure yy is a 4 digit date
        return None, True, DATE_YEAR_INCORRECTLY_FORMATTED

    try:
        ret_date = datetime.date(yy,mm,dd)
    except ValueError as msg:
        logging.debug('Could not make a datetime. Exception: %s' % msg)
        return None, True, str(msg) #<-- will send descriptive message of exact error (like month not in 1..12, etc)

    return ret_date, False, None

###############################################################################
##              BEGIN RAPIDSMS_XFORMS KEYWORD HANDLERS                       ##
##===========================================================================##
def pregnant_registration(session, xform):
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
    connection = session.connection

    #We must get the location from the Contact (Data Associate) who should be registered with this
    #phone number.  If the contact does not exist (unregistered) we throw an error.
    contactType, error = get_contacttype(session, 'da') #da = Data Associate
    if error:
        _send_msg(connection, NOT_A_DATA_ASSOCIATE)
        return True
    logging.debug('Data associate:: Connection: %s, Type: %s' % (connection, contactType))
    try:
        data_associate = Contact.objects.get(connection=connection, types=contactType)
    except ObjectDoesNotExist:
        logger.info("Data Associate Contact not found.  Mother cannot be correctly registered!")
        _send_msg(connection, NOT_REGISTERED_FOR_DATA_ASSOC)
        return True


    #get or create a new Mother Object without saving the object (and triggering premature errors)
    uid = _get_value_for_command('unique_id', xform)
    try:
        mother = PregnantMother.objects.get(uid=uid)
    except ObjectDoesNotExist:
        mother = PregnantMother()

    mother.first_name = _get_value_for_command('first_name', xform)
    mother.last_name = _get_value_for_command('last_name', xform)
    mother.uid = uid
    mother.high_risk_history = _get_value_for_command('high_risk_factor', xform)



    next_visit_dd = _get_value_for_command('next_visit_dd', xform)
    next_visit_mm = _get_value_for_command('next_visit_mm', xform)
    next_visit_yy = _get_value_for_command('next_visit_yy', xform)
    next_visit, error, error_msg = _make_date(next_visit_dd, next_visit_mm, next_visit_yy)
    date_dict = {
        "date_name": "Next Visit",
        "error_msg": error_msg,
        }
    session.template_vars.update(date_dict)
    if error:
        _send_msg(connection, DATE_ERROR, **session.template_vars)
        return True
    mother.next_visit = next_visit

    mother.reason_for_visit = _get_value_for_command('visit_reason', xform)
    zone_name = _get_value_for_command('zone', xform)


    lmp_dd = _get_value_for_command('lmp_dd', xform)
    lmp_mm = _get_value_for_command('lmp_mm', xform)
    lmp_yy = _get_value_for_command('lmp_yy', xform)
    lmp_date, error, error_msg = _make_date(lmp_dd, lmp_mm, lmp_yy)
    date_dict = {
        "date_name": "LMP",
        "error_msg": error_msg,
        }
    session.template_vars.update(date_dict)
    if error:
        _send_msg(connection, DATE_ERROR, **session.template_vars)
        return True
    mother.lmp = lmp_date


    lmp_dd = _get_value_for_command('edd_dd', xform)
    lmp_mm = _get_value_for_command('edd_mm', xform)
    lmp_yy = _get_value_for_command('edd_yy', xform)
    lmp_date, error, error_msg = _make_date(lmp_dd, lmp_mm, lmp_yy)
    date_dict = {
        "date_name": "EDD",
        "error_msg": error_msg,
        }
    session.template_vars.update(date_dict)
    if error:
        _send_msg(connection, DATE_ERROR, **session.template_vars)
        return True
    mother.edd = lmp_date

    logger.debug('Mother UID: %s' % mother.uid)

    #Create the mother model obj if it doesn't exist
    mother.location = data_associate.location
    if zone_name:
        mother.zone = _get_or_create_zone(mother.location, zone_name)

    mother.contact = data_associate
    mother.save()

    #Create a facility visit object and link it to the mother
    visit = FacilityVisit()
    visit.location = mother.location
    visit.visit_date = datetime.date.today()
    visit.reason_for_visit = 'initial_registration'
    visit.next_visit = mother.next_visit
    visit.mother = mother
    visit.contact = data_associate
    visit.save()

    _send_msg(connection, MOTHER_SUCCESS_REGISTERED, **session.template_vars)
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
    session = args['session']
    xform = args['xform']
    keyword = session.trigger.trigger_keyword

    logging.debug('Attempting to post-process submission. Keyword: %s  Session is: %s' % (keyword, session))

    try:
        kw_handler = XFormKeywordHandler.objects.get(keyword=keyword)
    except ObjectDoesNotExist:
        logger.debug('No keyword handler found for the xform submission with keyword: %s' % keyword)
        return
    func = to_function(kw_handler.function_path, True)
    session.template_vars = {} #legacy from using rapidsms-xforms
    logging.error('==================')
    logging.error(xform.top_level_tags())
    logging.error(dir(xform.top_level_tags()))
    for k,v in xform.top_level_tags().iteritems():
        session.template_vars[k] = v
#    session.template_vars.update(xform.top_level_tags) #this doesn't work for some reason
    #call the actual handling function
    return func(session, xform)

# then wire it to the xform_received signal
xform_saved_with_session.connect(handle_submission)