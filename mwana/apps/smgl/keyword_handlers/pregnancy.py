import logging
from mwana.apps.smgl.utils import get_value_from_form, send_msg,\
    make_date
from rapidsms.models import Contact
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.smgl.models import PregnantMother, FacilityVisit
from mwana.apps.smgl.app import NOT_REGISTERED_FOR_DATA_ASSOC
import datetime
from mwana.apps.contactsplus.models import ContactType
from mwana.apps.smgl import const
from mwana.apps.locations.models import Location, LocationType

logger = logging.getLogger(__name__)

def pregnant_registration(session, xform, router):
    """
    Handler for REG keyword (registration of pregnant mothers).
    Format:
    REG Mother_UID FIRST_NAME LAST_NAME HIGH_RISK_HISTORY FOLLOW_UP_DATE_dd FOLLOW_UP_DATE_mm FOLLOW_UP_DATE_yyyy \
        REASON_FOR_VISIT(ROUTINE/NON-ROUTINE) ZONE LMP_dd LMP_mm LMP_yyyy EDD_dd EDD_mm EDD_yyyy
    """
    logger.debug('Handling the REG keyword form')

    connection = session.connection

    # We must get the location from the Contact (Data Associate) who 
    # should be registered with this phone number.  If the contact does 
    # not exist (unregistered) we throw an error.
    contactType = ContactType.objects.get(slug__iexact=const.CTYPE_DATAASSOCIATE) #da = Data Associate
    try:
        data_associate = Contact.objects.get(connection=connection, types=contactType)
    except ObjectDoesNotExist:
        send_msg(connection, NOT_REGISTERED_FOR_DATA_ASSOC, router)
        return True


    # get or create a new Mother Object without saving the object 
    # (and triggering premature errors)
    
    # NOTE: this will currently overwrite whatever's there. 
    # confirm this is desired
    uid = get_value_from_form('unique_id', xform)
    try:
        mother = PregnantMother.objects.get(uid=uid)
    except ObjectDoesNotExist:
        mother = PregnantMother(uid=uid)
    
    
    mother.first_name = get_value_from_form('first_name', xform)
    mother.last_name = get_value_from_form('last_name', xform)
    mother.high_risk_history = get_value_from_form('high_risk_factor', xform)

    next_visit, error_msg = make_date(xform, "next_visit_dd", "next_visit_mm", "next_visit_yy")
    if error_msg:
        send_msg(connection, error_msg, router, **{"date_name": "Next Visit",
                                                   "error_msg": error_msg})
        return True
    
    mother.next_visit = next_visit
    mother.reason_for_visit = get_value_from_form('visit_reason', xform)
    zone_name = get_value_from_form('zone', xform)

    lmp_date, error_msg = make_date(xform, "lmp_dd", "lmp_mm", "lmp_yy", is_optional=True)
    if error_msg:
        send_msg(connection, error_msg, router,  **{"date_name": "LMP",
                                                    "error_msg": error_msg})
        return True

    edd_date, error_msg = make_date(xform, "edd_dd", "edd_mm", "edd_yy", is_optional=True)
    session.template_vars.update()
    if error_msg:
        send_msg(connection, error_msg, router, **{"date_name": "EDD",
                                                   "error_msg": error_msg})
        return True

    if lmp_date is None and edd_date is None:
        send_msg(connection, const.LMP_OR_EDD_DATE_REQUIRED, router)

    mother.lmp = lmp_date
    mother.edd = edd_date

    mother.location = data_associate.location
    if zone_name:
        try:
            mother.zone = Location.objects.get(type=LocationType.objects.get(slug__iexact=const.LOCTYPE_ZONE),
                                               slug__iexact=zone_name)
        except Location.DoesNotExist:
            send_msg(connection, const.UNKOWN_ZONE, router, zone=zone_name)
            return True

    mother.contact = data_associate
    mother.save()

    # Create a facility visit object and link it to the mother
    visit = FacilityVisit(location = mother.location,
                          visit_date = datetime.datetime.utcnow().date(),
                          reason_for_visit = 'initial_registration',
                          next_visit = mother.next_visit,
                          mother = mother,
                          contact = data_associate)
    visit.save()
    send_msg(connection, const.MOTHER_SUCCESS_REGISTERED, router, 
             **{"name": mother.contact.name, "unique_id": mother.uid})
    
    # if there is a lay counselor registered, also notify them
    for contact in get_laycounselors(mother):
        if contact.default_connection:
            send_msg(contact.default_connection, 
                     const.NEW_MOTHER_NOTIFICATION, router, 
                     **{"mother": mother.name, "unique_id": mother.uid})
        

    return True

def get_laycounselors(mother):
    """
    Given a mother, get the lay counselors who should be notified about
    her registration
    """
    # TODO: determine exactly how this should work.
    return Contact.objects.filter\
        (types=ContactType.objects.get(slug__iexact=const.CTYPE_LAYCOUNSELOR),
         location=mother.zone)
