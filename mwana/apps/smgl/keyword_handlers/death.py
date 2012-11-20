from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl.utils import (get_date, DateFormatError,
        get_session_message)
from mwana.apps.smgl.models import DeathRegistration
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required
import datetime


@registration_required
def death_registration(session, xform, router):
    """
    Keyword: death
    """

    name = session.connection.contact.name if session.connection.contact else ""
    get_session_message(session)

    try:
        date = get_date(xform, "death_date_dd", "death_date_mm", "death_date_yyyy")
    except DateFormatError, e:
        router.outgoing(OutgoingMessage(session.connection, str(e)))
        get_session_message(session, direction='O')
        return True

    if date > datetime.datetime.now().date():
        router.outgoing(OutgoingMessage(session.connection, const.DATE_MUST_BE_IN_PAST,
                 **{"date_name": "Date of Death", "date": date}))
        get_session_message(session, direction='O')
        return True

    contact = session.connection.contact
    unique_id = xform.xpath("form/unique_id")
    person = xform.xpath("form/death_type")
    if DeathRegistration.objects.filter(unique_id=unique_id, person=person):
        router.outgoing(OutgoingMessage(session.connection, const.DEATH_ALREADY_REGISTERED,
                 **{"unique_id": unique_id, "person": person}))
        get_session_message(session, direction='O')
        return True

    reg = DeathRegistration(contact=contact,
                            connection=session.connection,
                            session=session,
                            date=date,
                            unique_id=unique_id,
                            person=person,
                            place=xform.xpath("form/death_location"),
                            district=contact.get_current_district(),
                            facility=contact.get_current_facility()
                            )
    reg.save()
    resp = const.DEATH_REG_RESPONSE % {"name": name}
    router.outgoing(OutgoingMessage(session.connection, resp))
    get_session_message(session, direction='O')

