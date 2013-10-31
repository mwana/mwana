from mwana.apps.smgl.utils import (get_date, DateFormatError,
        respond_to_session)
from mwana.apps.smgl.models import DeathRegistration
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
import datetime


@registration_required
@is_active
def death_registration(session, xform, router):
    """
    Keyword: death
    """

    name = session.connection.contact.name if session.connection.contact else ""

    try:
        date = get_date(xform, "death_date_dd", "death_date_mm", "death_date_yyyy")
    except DateFormatError, e:
        return respond_to_session(router, session, str(e), is_error=True)

    if date > datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_PAST,
                                  is_error=True, **{"date_name": "Date of Death",
                                                    "date": date})

    contact = session.connection.contact
    unique_id = xform.xpath("form/unique_id")
    person = xform.xpath("form/death_type")
    if DeathRegistration.objects.filter(unique_id=unique_id, person=person):
        return respond_to_session(router, session, const.DEATH_ALREADY_REGISTERED,
                                  is_error=True, **{"unique_id": unique_id,
                                                    "person": person})

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
    return respond_to_session(router, session, const.DEATH_REG_RESPONSE,
                              **{"name": name,
                                 "unique_id":unique_id}
                              )
