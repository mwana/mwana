from mwana.apps.smgl.app import BIRTH_REG_RESPONSE
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl.utils import (make_date, mom_or_none,
        get_session_message, respond_to_session)
from mwana.apps.smgl.models import BirthRegistration, PregnantMother
from dimagi.utils.parsing import string_to_boolean
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
import datetime


@registration_required
@is_active
def birth_registration(session, xform, router):
    """
    Keyword: BIRTH
    """
    name = session.connection.contact.name if session.connection.contact else ""
    get_session_message(session)

    date, error = make_date(xform, "date_of_birth_dd", "date_of_birth_mm", "date_of_birth_yyyy")
    if error:
        return respond_to_session(router, session, error, is_error=True,
                                  **{"date_name": "Date of Birth"})

    if date > datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_PAST,
                                  is_error=True,
                                  **{"date_name": "Date of Birth", "date": date})

    num_kids = xform.xpath("form/num_children") or "t1"
    assert num_kids and num_kids[0] == "t"
    num_kids = int(num_kids[1:])

    try:
        mom = mom_or_none(xform.xpath("form/unique_id").lower())
    except PregnantMother.DoesNotExist:
        return respond_to_session(router, session, const.MOTHER_NOT_FOUND,
                                  is_error=True)

    contact = session.connection.contact
    reg = BirthRegistration(contact=contact,
                            connection=session.connection,
                            session=session,
                            date=date,
                            mother=mom,
                            gender=xform.xpath("form/gender"),
                            place=xform.xpath("form/birth_place"),
                            complications=string_to_boolean(xform.xpath("form/complications")),
                            number=num_kids,
                            district=contact.get_current_district(),
                            facility=contact.get_current_facility())
    reg.save()
    return respond_to_session(router, session, BIRTH_REG_RESPONSE,
                               **{"name": name})
