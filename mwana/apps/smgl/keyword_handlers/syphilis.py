from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl.utils import (make_date, mom_or_none,
        get_session_message, send_msg)
from mwana.apps.smgl.models import (SyphilisTest, SyphilisTreatment,
    PregnantMother)
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active
import datetime


@registration_required
@is_active
def syphilis(session, xform, router):
    """
    Handler for SYP keyword

    Used to record the statuss of the initial syphilis test
    status and treatment

    Format:
    SYP Mother_UID date_dd date_mm date_yyyy P/N/S[1-3] next_shot_dd next_shot_mm next_shot_yyyy
    """
    name = session.connection.contact.name if session.connection.contact else ""
    get_session_message(session)
    date, error_msg = make_date(xform,
                        "date_dd", "date_mm", "date_yyyy"
                        )
    if error_msg:
        send_msg(session.connection, error_msg, router,
                 **{"date_name": "Test Date", "error_msg": error_msg})
        return True

    if date > datetime.datetime.now().date():
        router.outgoing(OutgoingMessage(session.connection, const.DATE_MUST_BE_IN_PAST,
                 **{"date_name": "Test Date", "date": date}))
        get_session_message(session, direction='O')
        return True
    status = xform.xpath("form/status")
    unique_id = xform.xpath("form/unique_id")
    try:
        mom = mom_or_none(unique_id)
    except PregnantMother.DoesNotExist:
        router.outgoing(OutgoingMessage(session.connection, const.MOTHER_NOT_FOUND))
        get_session_message(session, direction='O')
        return True
    if status in ['p', 'n']:
        # register syp test results
        syp_test = SyphilisTest(session=session,
                               date=date,
                               mother=mom,
                               result=status
                               )
        syp_test.save()
        resp = const.SYP_TEST_COMPLETE % {"name": name, "unique_id": unique_id}
    else:
        # register syp treatment information
        next_visit_date, error_msg = make_date(xform,
                            "next_visit_date_dd", "next_visit_date_mm", "next_visit_date_yyyy",
                            is_optional=True
                            )
        if error_msg:
            send_msg(session.connection, error_msg, router,
                     **{"date_name": "Next Shot Date", "error_msg": error_msg})
            return True

        if next_visit_date and next_visit_date < datetime.datetime.now().date():
            router.outgoing(OutgoingMessage(session.connection, const.DATE_MUST_BE_IN_FUTURE,
                     **{"date_name": "Next Shot Date", "date": next_visit_date}))
            get_session_message(session, direction='O')
            return True
        syp_treatment = SyphilisTreatment(session=session,
                               date=date,
                               mother=mom,
                               shot_number=status,
                               next_visit_date=next_visit_date
                               )
        syp_treatment.save()
        resp = const.SYP_TREATMENT_COMPLETE % {"name": name, "unique_id": unique_id}

    router.outgoing(OutgoingMessage(session.connection, resp))
    get_session_message(session, direction='O')
