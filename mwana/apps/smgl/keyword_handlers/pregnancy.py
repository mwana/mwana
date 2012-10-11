import logging
from mwana.apps.smgl.utils import get_value_from_form, send_msg,\
    make_date
from rapidsms.models import Contact
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.smgl.models import PregnantMother, FacilityVisit
import datetime
from mwana.apps.contactsplus.models import ContactType
from mwana.apps.smgl import const
from mwana.apps.locations.models import Location, LocationType
from mwana.apps.smgl.decorators import registration_required

logger = logging.getLogger(__name__)


@registration_required
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
    contactType = ContactType.objects.get(slug__iexact=const.CTYPE_DATACLERK)  # da = Data Associate
    try:
        data_associate = Contact.objects.get(connection=connection, types=contactType)
    except ObjectDoesNotExist:
        send_msg(connection, const.NOT_REGISTERED_FOR_DATA_ASSOC, router)
        return True

    # get or create a new Mother Object without saving the object
    # (and triggering premature errors)
    uid = get_value_from_form('unique_id', xform)
    if PregnantMother.objects.filter(uid=uid).count():
        send_msg(connection, const.DUPLICATE_REGISTRATION, router,
                 **{"unique_id": uid})
        return True

    mother = PregnantMother(uid=uid)
    mother.created_date = session.modified_time

    mother.first_name = get_value_from_form('first_name', xform)
    mother.last_name = get_value_from_form('last_name', xform)

    next_visit, error_msg = make_date(xform, "next_visit_dd", "next_visit_mm", "next_visit_yy")
    if error_msg:
        send_msg(connection, error_msg, router, **{"date_name": "Next Visit",
                                                   "error_msg": error_msg})
        return True

    if next_visit < datetime.datetime.now().date():
        send_msg(connection, const.DATE_MUST_BE_IN_FUTURE, router,
                 **{"date_name": "Next Visit", "date": next_visit})
        return True

    mother.next_visit = next_visit
    mother.reason_for_visit = get_value_from_form('visit_reason', xform)
    zone_name = get_value_from_form('zone', xform)

    lmp_date, error_msg = make_date(xform, "lmp_dd", "lmp_mm", "lmp_yy", is_optional=True)
    if error_msg:
        send_msg(connection, error_msg, router,  **{"date_name": "LMP",
                                                    "error_msg": error_msg})
        return True

    if lmp_date and lmp_date > datetime.datetime.now().date():
        send_msg(connection, const.DATE_MUST_BE_IN_PAST, router,
                 **{"date_name": "LMP", "date": lmp_date})
        return True

    edd_date, error_msg = make_date(xform, "edd_dd", "edd_mm", "edd_yy", is_optional=True)
    session.template_vars.update()
    if error_msg:
        send_msg(connection, error_msg, router, **{"date_name": "EDD",
                                                   "error_msg": error_msg})
        return True

    if edd_date and edd_date < datetime.datetime.now().date():
        send_msg(connection, const.DATE_MUST_BE_IN_FUTURE, router,
                 **{"date_name": "EDD", "date": edd_date})
        return True

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

    reasons = xform.xpath("form/high_risk_factor")
    if reasons:
        for r in reasons.split(" "):
            mother.set_risk_reason(r)

    mother.contact = data_associate
    mother.save()

    send_msg(connection, const.MOTHER_SUCCESS_REGISTERED, router,
             **{"name": mother.contact.name, "unique_id": mother.uid})

    # if there is a lay counselor(s) registered, also notify them
    for contact in mother.get_laycounselors():
        if contact.default_connection:
            send_msg(contact.default_connection,
                     const.NEW_MOTHER_NOTIFICATION, router,
                     **{"mother": mother.name, "unique_id": mother.uid})

    return True


@registration_required
def follow_up(session, xform, router):
    """
    Keyword handler for follow up visits.
    """
    connection = session.connection
    dc_type = ContactType.objects.get(slug__iexact=const.CTYPE_DATACLERK)
    try:
        contact = Contact.objects.get(types=dc_type, connection=connection)
    except ObjectDoesNotExist:
        send_msg(connection, const.NOT_A_DATA_ASSOCIATE, router, **session.template_vars)
        return True

    unique_id = get_value_from_form('unique_id', xform)
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        send_msg(connection, const.FUP_MOTHER_DOES_NOT_EXIST, router)
        return True

    edd_date, error_msg = make_date(xform, "edd_dd", "edd_mm", "edd_yy", is_optional=True)
    if error_msg:
        send_msg(connection, error_msg, router, **{"date_name": "EDD",
                                                   "error_msg": error_msg})
        return True

    if edd_date and edd_date < datetime.datetime.now().date():
        send_msg(connection, const.DATE_MUST_BE_IN_FUTURE, router,
                 **{"date_name": "EDD", "date": edd_date})
        return True

    visit_reason = get_value_from_form('visit_reason', xform)
    next_visit, error_msg = make_date(xform, "next_visit_dd", "next_visit_mm", "next_visit_yy")
    if error_msg:
        send_msg(connection, error_msg, router, **{"date_name": "Next Visit",
                                                   "error_msg": error_msg})
        return True

    if next_visit < datetime.datetime.now().date():
        send_msg(connection, const.DATE_MUST_BE_IN_FUTURE, router,
                 **{"date_name": "Next Visit", "date": next_visit})
        return True

    # Make the follow up facility visit
    visit = FacilityVisit()
    visit.mother = mother
    visit.contact = contact
    visit.location = contact.location
    visit.edd = edd_date
    visit.reason_for_visit = visit_reason
    visit.next_visit = next_visit
    visit.visit_date = datetime.datetime.utcnow().date()
    visit.created_date = session.modified_time
    visit.save()

    send_msg(connection, const.FOLLOW_UP_COMPLETE, router, name=contact.name, unique_id=mother.uid)


@registration_required
def told(session, xform, router):
    # TODO: processing, if necessary
    if not session.connection.contact:
        send_msg(session.connection, const.NOT_REGISTERED_FOR_DATA_ASSOC, router,
                 name=session.connection.contact.name)
        return True

    send_msg(session.connection, const.TOLD_COMPLETE, router,
             name=session.connection.contact.name)
    return True
