from mwana.apps.smgl.app import BIRTH_REG_RESPONSE
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl.utils import get_date, DateFormatError
from mwana.apps.smgl.models import BirthRegistration
from dimagi.utils.parsing import string_to_boolean

def birth_registration(session, xform, router):
    """
    Keyword: BIRTH
    """
    name = session.connection.contact.name if session.connection.contact else ""
    
    try:
        date = get_date(xform, "date_of_birth_dd", "date_of_birth_mm", "date_of_birth_yyyy")
    except DateFormatError:
        # TODO
        pass
        raise
    num_kids = xform.xpath("form/num_children") or "t1"
    assert num_kids and num_kids[0] == "t"
    num_kids = int(num_kids[1:])
    reg = BirthRegistration(contact=session.connection.contact,
                            connection=session.connection,
                            date=date,
                            unique_id=xform.xpath("form/unique_id"),
                            gender=xform.xpath("form/gender"),
                            place=xform.xpath("form/birth_place"),
                            complications=string_to_boolean(xform.xpath("form/complications")),
                            number=num_kids)
    reg.save()      
    resp = BIRTH_REG_RESPONSE % {"name": name}
    router.outgoing(OutgoingMessage(session.connection, resp))
    