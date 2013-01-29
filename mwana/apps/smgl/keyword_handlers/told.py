import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist

from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
from mwana.apps.smgl.models import (PregnantMother, FacilityVisit,
    ToldReminder, BirthRegistration, Referral)
from mwana.apps.smgl.utils import (get_value_from_form, respond_to_session)

from mwana.apps.smgl.const import TOLD_COMPLETE
logger = logging.getLogger(__name__)


@registration_required
@is_active
def told(session, xform, router):
    """
    Handler for TOLD keyword (Used to notify the system when a mother is reminded).

    Format:
    TOLD Mother_UID EDD/NVD/REF
    """
    logger.debug('Handling the TOLD keyword form')
    connection = session.connection

    if not connection.contact:
        return respond_to_session(router, session, const.NOT_REGISTERED_FOR_DATA_ASSOC,
                                  is_error=True)

    unique_id = get_value_from_form('unique_id', xform)
    reminder_type = get_value_from_form('reminder_type', xform)
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        return respond_to_session(router, session, const.FUP_MOTHER_DOES_NOT_EXIST,
                                  is_error=True)
    else:
        now = datetime.datetime.now()
        if reminder_type == 'edd':
            reg = BirthRegistration.objects.filter(mother=mother)
            if reg:
                return respond_to_session(router, session,
                                          const.TOLD_MOTHER_HAS_ALREADY_DELIVERED,
                                          is_error=True, **{'unique_id': unique_id})
        elif reminder_type == 'ref':
            refs = Referral.objects.filter(date__gte=now, mother=mother)
            if not refs:
                return respond_to_session(router, session, const.TOLD_MOTHER_HAS_NO_REF,
                                          is_error=True, **{'unique_id': unique_id})
        else:
            if reminder_type == 'nvd':
                reminder_type = 'anc'
            visits = FacilityVisit.objects.filter(next_visit__gte=now.date(),
                                                  mother=mother,
                                                  visit_type=reminder_type)
            if not visits:
                return respond_to_session(router, session, 
                                          const.TOLD_MOTHER_HAS_NO_NVD,
                                          is_error=True, 
                                          **{'unique_id': unique_id})
        # Generate the TOLD Reminder database entry
        ToldReminder.objects.create(
                            contact=connection.contact,
                            mother=mother,
                            session=session,
                            date=session.modified_time,
                            type=reminder_type,
                            )
        return respond_to_session(router, session, TOLD_COMPLETE, 
                                  **{'name': connection.contact.name})
