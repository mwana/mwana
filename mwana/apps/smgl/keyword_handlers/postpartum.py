import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist

from rapidsms.models import Contact

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
from mwana.apps.smgl.models import PregnantMother, FacilityVisit, BirthRegistration
from mwana.apps.smgl.utils import get_value_from_form, make_date, respond_to_session

logger = logging.getLogger(__name__)

@registration_required
@is_active
def postpartum_visit(session, xform, router):
    """
    Handler for PP keyword

    Used to record a post-partum vist

    Format:
    PP Mother_UID WELL/SICK WELL/SICK YES/NO NVD_dd NVD_mm NVD_yyyy
    """
    connection = session.connection
    c_types = ContactType.objects.filter(
                           slug__in=[const.CTYPE_DATACLERK,
                                     const.CTYPE_LAYCOUNSELOR]
                        )
    try:
        contact = Contact.objects.get(types__in=c_types, connection=connection)
    except ObjectDoesNotExist:
        return respond_to_session(router, session, const.NOT_A_DATA_ASSOCIATE, 
                                  is_error=True)

    unique_id = get_value_from_form('unique_id', xform)
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        return respond_to_session(router, session, const.PP_MOTHER_DOES_NOT_EXIST,
                                  is_error=True)

    # Ensure mother has delivered
    try:
        BirthRegistration.objects.get(mother=mother)
    except ObjectDoesNotExist:
        return respond_to_session(router, session, const.PP_MOTHER_HAS_NOT_DELIVERED,
                                  is_error=True)

    next_visit, error_msg = make_date(xform,
                        "next_visit_dd", "next_visit_mm", "next_visit_yy",
                        is_optional=True,
                        )
    if error_msg:
        return respond_to_session(router, session, error_msg, is_error=True,
                                  **{"date_name": "Next Visit"})

    if next_visit:
        if next_visit < datetime.datetime.now().date():
            return respond_to_session(router, session, const.DATE_MUST_BE_IN_FUTURE,
                                      is_error=True, **{"date_name": "Next Visit",
                                                        "date": next_visit})
    else:
        pos_visits = FacilityVisit.objects.filter(mother=mother, visit_type="pos")
        if pos_visits.count() < 2:
            return respond_to_session(router, session, const.PP_NVD_REQUIRED,
                                      is_error=True, **{"num": pos_visits.count()})

    mother_status = get_value_from_form('mother_status', xform)
    baby_status = get_value_from_form('baby_status', xform)
    referred = get_value_from_form('referred', xform)

    # Make the follow up facility visit
    visit = FacilityVisit()
    visit.mother = mother
    visit.contact = contact
    visit.location = contact.location
    visit.visit_date = datetime.datetime.utcnow().date()
    visit.created_date = session.modified_time
    visit.visit_type = 'pos'
    visit.mother_status = mother_status
    visit.baby_status = baby_status
    if referred == 'yes':
        visit.referred = True
    if next_visit:
        visit.next_visit = next_visit
    visit.save()

    return respond_to_session(router, session, const.PP_COMPLETE,
                              **{'name': contact.name, 'unique_id': mother.uid})
