from mwana.apps.smgl.app import BIRTH_REG_RESPONSE
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl.utils import make_date, mom_or_none
from mwana.apps.smgl.models import BirthRegistration, PregnantMother
from dimagi.utils.parsing import string_to_boolean
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required
import datetime


@registration_required
def birth_registration(session, xform, router):
    """
    Keyword: BIRTH
    """
    name = session.connection.contact.name if session.connection.contact else ""

    date, error = make_date(xform, "date_of_birth_dd", "date_of_birth_mm", "date_of_birth_yyyy")
    if error:
        router.outgoing(OutgoingMessage(session.connection, error,
                                        **{"date_name": "Date of Birth",
                                           "error_msg": error}))
        return True

    if date > datetime.datetime.now().date():
        router.outgoing(OutgoingMessage(session.connection, const.DATE_MUST_BE_IN_PAST,
                 **{"date_name": "Date of Birth", "date": date}))
        return True

    num_kids = xform.xpath("form/num_children") or "t1"
    assert num_kids and num_kids[0] == "t"
    num_kids = int(num_kids[1:])

    try:
        mom = mom_or_none(xform.xpath("form/unique_id").lower())
    except PregnantMother.DoesNotExist:
        router.outgoing(OutgoingMessage(session.connection, const.MOTHER_NOT_FOUND))
        return True

    reg = BirthRegistration(contact=session.connection.contact,
                            connection=session.connection,
                            date=date,
                            mother=mom,
                            gender=xform.xpath("form/gender"),
                            place=xform.xpath("form/birth_place"),
                            complications=string_to_boolean(xform.xpath("form/complications")),
                            number=num_kids,
                            district=session.connection.contact.get_current_district())
    reg.save()
    resp = BIRTH_REG_RESPONSE % {"name": name}
    router.outgoing(OutgoingMessage(session.connection, resp))

