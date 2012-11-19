import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist

from rapidsms.models import Contact

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required
from mwana.apps.smgl.models import PregnantMother, FacilityVisit, BirthRegistration
from mwana.apps.smgl.utils import get_value_from_form, send_msg, make_date

logger = logging.getLogger(__name__)


@registration_required
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
        send_msg(connection, const.NOT_A_DATA_ASSOCIATE, router, **session.template_vars)
        return True

    unique_id = get_value_from_form('unique_id', xform)
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        send_msg(connection, const.PP_MOTHER_DOES_NOT_EXIST, router)
        return True

    # Ensure mother has delivered
    try:
        BirthRegistration.objects.get(mother=mother)
    except ObjectDoesNotExist:
        send_msg(connection, const.PP_MOTHER_HAS_NOT_DELIVERED)
        return True

    next_visit, error_msg = make_date(xform,
                        "next_visit_dd", "next_visit_mm", "next_visit_yy",
                        is_optional=True,
                        )
    if error_msg:
        send_msg(connection, error_msg, router, **{"date_name": "Next Visit",
                                                   "error_msg": error_msg})
        return True

    if next_visit:
        if next_visit < datetime.datetime.now().date():
            send_msg(connection, const.DATE_MUST_BE_IN_FUTURE, router,
                     **{"date_name": "Next Visit", "date": next_visit})
            return True
    else:
        pos_visits = FacilityVisit.objects.filter(mother=mother, visit_type="pos")
        if pos_visits.count() < 2:
            send_msg(connection, const.PP_NVD_REQUIRED, router,
                     **{"num": pos_visits.count()})
            return True

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

    send_msg(connection, const.PP_COMPLETE, router, name=contact.name, unique_id=mother.uid)
