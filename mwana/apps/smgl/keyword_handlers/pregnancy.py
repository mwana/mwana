import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist

from rapidsms.models import Contact

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.locations.models import Location, LocationType
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
from mwana.apps.smgl.models import PregnantMother, FacilityVisit
from mwana.apps.smgl.utils import (get_value_from_form, send_msg, make_date,
    respond_to_session, get_district_facility_zone)

logger = logging.getLogger(__name__)


@registration_required
@is_active
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
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True)

    # get or create a new Mother Object without saving the object
    # (and triggering premature errors)
    uid = get_value_from_form('unique_id', xform)
    if PregnantMother.objects.filter(uid=uid).count():
        return respond_to_session(router, session, const.DUPLICATE_REGISTRATION,
                                  is_error=True, **{"unique_id": uid})

    mother = PregnantMother(uid=uid)
    mother.created_date = session.modified_time

    mother.first_name = get_value_from_form('first_name', xform)
    mother.last_name = get_value_from_form('last_name', xform)

    next_visit, error_msg = make_date(xform, "next_visit_dd", "next_visit_mm", "next_visit_yy")
    if error_msg:
        return respond_to_session(router, session, error_msg,
                                  is_error=True, **{"date_name": "Next Visit"})

    if next_visit < datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_FUTURE,
                                  is_error=True, **{"date_name": "Next Visit",
                                                    "date": next_visit})

    mother.next_visit = next_visit
    mother.reason_for_visit = get_value_from_form('visit_reason', xform)
    zone_name = get_value_from_form('zone', xform)

    lmp_date, error_msg = make_date(xform, "lmp_dd", "lmp_mm", "lmp_yy", is_optional=True)
    if error_msg:
        return respond_to_session(router, session, error_msg,
                                  is_error=True, **{"date_name": "LMP"})

    if lmp_date and lmp_date > datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_PAST,
                                  is_error=True, **{"date_name": "LMP",
                                                    "date": lmp_date})

    edd_date, error_msg = make_date(xform, "edd_dd", "edd_mm", "edd_yy", is_optional=True)
    session.template_vars.update()
    if error_msg:
        return respond_to_session(router, session, error_msg,
                                  is_error=True, **{"date_name": "EDD"})

    if edd_date and edd_date < datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_FUTURE,
                                  is_error=True, **{"date_name": "EDD",
                                                    "date": edd_date})
    mother.lmp = lmp_date
    mother.edd = edd_date

    mother.location = data_associate.location
    if zone_name:
        try:
            mother.zone = Location.objects.get(type=LocationType.objects.get(slug__iexact=const.LOCTYPE_ZONE),
                                               slug__iexact=zone_name)
        except Location.DoesNotExist:
            #See if this is a village
            try:
                village = Location.objects.get(type=LocationType.objects.get(slug__iexact=const.LOCTYPE_VILLAGE),
                    slug=zone_name)
                mother.village = village
                mother.zone = village.parent
            except Location.DoesNotExist:
                return respond_to_session(router, session, const.UNKOWN_ZONE,
                                          is_error=True, **{"zone": zone_name})

    reasons = xform.xpath("form/high_risk_factor")
    if reasons:
        for r in reasons.split(" "):
            mother.set_risk_reason(r)

    mother.contact = data_associate
    mother.save()

    #We will also create a Facility Visit object here
    #Is this right?
    facility_visit = FacilityVisit.objects.create(
        created_date=session.modified_time,
        mother=mother,
        location=connection.contact.location,
        visit_date=datetime.datetime.today(),
        visit_type='anc',
        reason_for_visit='reg',
        edd=edd_date,
        next_visit=next_visit,
        contact=connection.contact,
        )

    # if there is a lay counselor(s) registered, also notify them
    for contact in mother.get_laycounselors():
        if contact.default_connection:
            send_msg(contact.default_connection,
                     const.NEW_MOTHER_NOTIFICATION, router,
                     **{"mother": mother.name, "unique_id": mother.uid})

    return respond_to_session(router, session, const.MOTHER_SUCCESS_REGISTERED,
                              **{"name": mother.contact.name,
                                 "unique_id": mother.uid})

@registration_required
@is_active
def follow_up(session, xform, router):
    """
    Keyword handler for follow up visits.
    """
    connection = session.connection
    dc_type = ContactType.objects.get(slug__iexact=const.CTYPE_DATACLERK)
    try:
        contact = Contact.objects.get(types=dc_type, connection=connection)
    except ObjectDoesNotExist:
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True)

    unique_id = get_value_from_form('unique_id', xform)
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        return respond_to_session(router, session, const.FUP_MOTHER_DOES_NOT_EXIST, **{"unique_id":unique_id})

    edd_date, error_msg = make_date(xform, "edd_dd", "edd_mm", "edd_yy", is_optional=True)
    if error_msg:
        return respond_to_session(router, session, error_msg,
                                  is_error=True, **{"date_name": "EDD"})

    if edd_date and edd_date < datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_FUTURE,
                                  is_error=True, **{"date_name": "EDD",
                                                    "date": edd_date})

    visit_reason = get_value_from_form('visit_reason', xform)
    next_visit, error_msg = make_date(xform, "next_visit_dd", "next_visit_mm", "next_visit_yy")
    if error_msg:
        return respond_to_session(router, session, error_msg,
                                  is_error=True, **{"date_name": "Next Visit"})

    if next_visit < datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_FUTURE,
                                  is_error=True, **{"date_name": "Next Visit",
                                                    "date": next_visit})

    # Create the facility visit
    visit = FacilityVisit()
    visit.mother = mother
    visit.contact = contact
    visit.location = contact.location
    visit.edd = edd_date
    visit.reason_for_visit = visit_reason
    visit.next_visit = next_visit
    visit.visit_date = datetime.datetime.utcnow().date()
    visit.created_date = session.modified_time
    visit.visit_type = 'anc'
    visit.save()

    return respond_to_session(router, session, const.FOLLOW_UP_COMPLETE,
                              **{'name': contact.name, 'unique_id': mother.uid})

@registration_required
@is_active
def motherid_lookup(session, xform, router):
    """
    Handler for LOOK keyword
    Used to query the database to obtain safe motherhood number

    Format:
    LOOK F_NAME L_NAME ZONE_ID
    """
    logger.debug('Handling the LOOK keyword form')
    connection = session.connection

    if not connection.contact:
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True)

    f_name = get_value_from_form('f_name', xform)
    l_name = get_value_from_form('l_name', xform)
    zone_id = get_value_from_form('zone_id', xform)
    try:
        mother = PregnantMother.objects.get(first_name__iexact=f_name,
                                            last_name__iexact=l_name,
                                            zone__slug=zone_id)
    except ObjectDoesNotExist:
        # NOTE: should this be an error?
        return respond_to_session(router, session, const.LOOK_MOTHER_DOES_NOT_EXIST,
            **{'first_name':f_name, 'last_name':l_name})
    else:
        return respond_to_session(router, session, const.LOOK_COMPLETE,
                                  **{'unique_id': mother.uid})
