import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist

from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
from mwana.apps.smgl.models import (PregnantMother, FacilityVisit,
    ToldReminder, BirthRegistration, Referral)
from mwana.apps.smgl.utils import (get_value_from_form, send_msg,
                get_session_message)
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
    get_session_message(session)

    if not connection.contact:
        send_msg(connection, const.NOT_REGISTERED_FOR_DATA_ASSOC, router,
                 name=connection.contact.name)
        get_session_message(session, direction='O')

        return True

    unique_id = get_value_from_form('unique_id', xform)
    reminder_type = get_value_from_form('reminder_type', xform)
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        send_msg(connection, const.FUP_MOTHER_DOES_NOT_EXIST, router)
        get_session_message(session, direction='O')

        return True
    else:
        now = datetime.datetime.now()
        if reminder_type == 'edd':
            reg = BirthRegistration.objects.filter(mother=mother)
            if reg:
                msg = const.TOLD_MOTHER_HAS_ALREADY_DELIVERED % {
                                                        'unique_id': unique_id
                                                        }
                send_msg(connection, msg, router)
                get_session_message(session, direction='O')
                return True
        elif reminder_type == 'ref':
            refs = Referral.objects.filter(date__gte=now, mother=mother)
            if not refs:
                msg = const.TOLD_MOTHER_HAS_NO_REF % {'unique_id': unique_id}
                send_msg(connection, msg, router)
                get_session_message(session, direction='O')
                return True
        else:
            if reminder_type == 'nvd':
                reminder_type = 'anc'
            visits = FacilityVisit.objects.filter(next_visit__gte=now.date(),
                                                  mother=mother,
                                                  visit_type=reminder_type)
            if not visits:
                msg = const.TOLD_MOTHER_HAS_NO_NVD % {'unique_id': unique_id}
                send_msg(connection, msg, router)
                get_session_message(session, direction='O')
                return True
        # Generate the TOLD Reminder database entry
        ToldReminder.objects.create(
                            contact=connection.contact,
                            mother=mother,
                            session=session,
                            date=session.modified_time,
                            type=reminder_type,
                            )
        send_msg(connection, const.TOLD_COMPLETE, router,
                 name=connection.contact.name)
        get_session_message(session, direction='O')

    return True
