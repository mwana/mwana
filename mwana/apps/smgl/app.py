import logging
from rapidsms.apps.base import AppBase

from .models import XFormKeywordHandler

from mwana.apps.agents.handlers.agent import get_unique_value
from mwana.apps.locations.models import Location, LocationType
from mwana.apps.smgl.models import AmbulanceRequest
from mwana import const as mwanaconst

from rapidsms.models import Contact
from rapidsms.messages import OutgoingMessage

from dimagi.utils.modules import to_function

from django.core.exceptions import ObjectDoesNotExist
from smscouchforms.signals import xform_saved_with_session
from mwana.apps.smgl.utils import get_contacttype, send_msg,\
    get_value_from_form, make_date
from mwana.apps.smgl import const
from mwana.apps.contactsplus.models import ContactType

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

# Begin Translatable messages
FACILITY_NOT_RECOGNIZED = _("Sorry, the facility '%(facility)s' is not recognized. Please try again.")
ALREADY_REGISTERED = _("%(name)s, you are already registered as a %(readable_user_type)s at %(facility)s but your details have been updated")
CONTACT_TYPE_NOT_RECOGNIZED = _("Sorry, the User Type '%(title)s' is not recognized. Please try again.")
ZONE_SPECIFIED_BUT_NOT_CBA = _("You can not specify a zone when registering as a %(reg_type)s!")
USER_SUCCESS_REGISTERED = _("Thank you for registering! You have successfully registered as a %(readable_user_type)s at %(facility)s.")
NOT_PREREGISTERED = _('Sorry, you are not on the pre-registered users list. Please contact ZCAHRD for assistance')
DATE_ERROR = _('%(error_msg)s for %(date_name)s')
INITIAL_AMBULANCE_RESPONSE = _('Thank you.Your request for an ambulance has been received. Someone will be in touch with you shortly.If no one contacts you,please call the emergency number!')
ER_TO_DRIVER = _("Mother with ID:%(unique_id)s needs ER.Location:%(from_location)s,contact num:%(sender_phone_number)s. Plz SEND 'RESP %(unique_id)s OTW, DL, or NA' if you see this")
ER_TO_TRIAGE_NURSE = _("Mother with ID:%(unique_id)s needs ER.Location:%(from_location)s,contact num:%(sender_phone_number)s. Plz SEND 'RESP %(unique_id)s OTW, DL, or NA' if you see this")
ER_CONFIRM_SESS_NOT_FOUND = _("The Emergency with ID:%(unique_id)s can not be found! Please try again or contact your DMO immediately.")
NOT_REGISTERED_TO_CONFIRM_ER = _("Sorry. You are not registered as Triage Nurse, Ambulance or DMO")
THANKS_ER_CONFIRM = _("Thank you for confirming. When you know the status of the Ambulance, please send RESP <RESPONSE_TYPE>!")
NOT_ALLOWED_ER_WORKFLOW = _("Sorry, your registration type is not allowed to send Emergency Response type messages")
AMB_RESPONSE_THANKS = _("Thank you. The ambulance for this request has been marked as %(response)s. We will notify the Rural Facility.")
AMB_CANT_FIND_UID = _("Sorry. We cannot find the Mother's Unique ID you specified. Please try again or contact the DMO")
AMB_RESPONSE_NOT_AVAILABLE = _("Ambulance is %(status)s for Request with ID:%(unique_id)s needs ER.Location:%(from_location)s,contact num:%(sender_phone_number)s. Please respond accordingly.")
AMB_RESPONSE_ORIGINATING_LOCATION_INFO = _("Emergency Response: The ambulance for the Unique ID: %(unique_id)s has been marked %(response)s")
AMB_OUTCOME_NO_OUTCOME = _("No OUTCOME Specified.  Please send an outcome!")
AMB_OUTCOME_MSG_RECEIVED = _("Thanks for your message! We have marked the patient with unique_id %(unique_id)s as outcome: %(outcome)s")
AMB_OUTCOME_ORIGINATING_LOCATION_INFO = _("We have been notified of the patient outcome for patient with unique_id: %(unique_id)s. Outcome: %(outcome)s")
AMB_OUTCOME_FILED = _("A patient outcome for an Emergency Response for Patient (%(unique_id)s) has been filed by %(name)s (%(contact_type)s)")
ER_TO_CLINIC_WORKER = _("Emergency Response has occured for Mother with Unique ID: %(unique_id)s. Expect a patient.")
ER_STATUS_UPDATE = _("The Emergency Request for Mother with Unique ID: %(unique_id)s has been marked %(status)s by %(name)s (%(confirm_type)s)")


BIRTH_REG_RESPONSE = _("Thanks %(name)s! the Facility/Community birth has been registered.")


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


def _generate_uid_for_er():
    #grab all the existing amb requests that have made up UIDs:
    ers = AmbulanceRequest.objects.filter(mother_uid__icontains='A')

    if not ers.count():
        uid = 'A1'
    else:
        counter = ers.count()
        uids = ers.values_list('mother_uid')
        uids = map(lambda x: x[0], uids)  # gets us a nice list of uids
        uid = 'A%s' % counter  # starting point
        counter += 1
        while uid in uids:  # iterate until we find a good UID
            uid = 'A%s' % counter
            counter += 1
    return uid


# Taken from mwana.apps.agents.handler.agrent.AgentHandler
def _get_or_create_zone(clinic, name):
    # create the zone if it doesn't already exist
    zone_type, _ = LocationType.objects.get_or_create(slug=mwanaconst.ZONE_SLUGS[0])
    return Location.objects.get_or_create(name__iexact=name,
                                parent=clinic,
                                type=zone_type,
                                defaults={
                                    'name': name,
                                    'slug': get_unique_value(Location.objects, "slug", name),
                                })


def _get_allowed_ambulance_workflow_contact(session):
    connection = session.connection
    legal_types = ['tn', 'am', 'dmo', 'worker']
    try:
        contact = Contact.objects.get(connection=connection, types__slug__in=legal_types)
        return contact
    except ObjectDoesNotExist:
        return None


###############################################################################
##              BEGIN RAPIDSMS_XFORMS KEYWORD HANDLERS                       ##
##===========================================================================##

###############################################################################


# define a listener
def handle_submission(sender, **args):
    session = args['session']
    xform = args['xform']
    router = args['router']
    xform.initiating_phone_number = session.connection.identity
    keyword = session.trigger.trigger_keyword

    logger.debug('Attempting to post-process submission. Keyword: %s  Session is: %s' % (keyword, session))

    try:
        kw_handler = XFormKeywordHandler.objects.get(keyword=keyword)
    except ObjectDoesNotExist:
        logger.debug('No keyword handler found for the xform submission with keyword: %s' % keyword)
        return

    try:
        func = to_function(str(kw_handler.function_path), True)
        session.template_vars = {}  # legacy from using rapidsms-xforms
        for k, v in xform.top_level_tags().iteritems():
            session.template_vars[k] = v

        # call the actual handling function
        return func(session, xform, router)
    except Exception:
        # assume that we were supposed to deal with this but something
        # unexpected went wrong. Respond with a general default
        # TODO: should we also mark the form somehow as errored out?
        logging.exception("Problem processing message in session %s from %s." % \
                          (session, session.connection))
        router.outgoing(OutgoingMessage(session.connection,
                                        const.GENERAL_ERROR))
        return True

# then wire it to the xform_received signal
xform_saved_with_session.connect(handle_submission)
