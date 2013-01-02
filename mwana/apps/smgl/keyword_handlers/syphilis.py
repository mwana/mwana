import datetime

from mwana.apps.smgl.utils import (make_date, mom_or_none,
        get_session_message, get_current_district, respond_to_session)
from mwana.apps.smgl.models import (SyphilisTest, SyphilisTreatment,
    PregnantMother)
from mwana.apps.smgl import const
from mwana.apps.smgl.decorators import registration_required, is_active


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
        return respond_to_session(router, session, error_msg, is_error=True,
                                  **{"date_name": "Test Date"})

    if date > datetime.datetime.now().date():
        return respond_to_session(router, session, const.DATE_MUST_BE_IN_PAST,
                                  is_error=True, **{"date_name": "Test Date",
                                                    "date": date})
    status = xform.xpath("form/status")
    unique_id = xform.xpath("form/unique_id")
    try:
        mom = mom_or_none(unique_id)
    except PregnantMother.DoesNotExist:
        return respond_to_session(router, session, const.MOTHER_NOT_FOUND)
    contact = session.connection.contact
    district = get_current_district(contact.location)
    if status in ['p', 'n']:
        # register syp test results
        syp_test = SyphilisTest(session=session,
                               date=date,
                               mother=mom,
                               result=status,
                               district=district
                               )
        syp_test.save()
        return respond_to_session(router, session, const.SYP_TEST_COMPLETE,
                                  **{"name": name, "unique_id": unique_id})

    else:
        # register syp treatment information
        next_visit_date, error_msg = make_date(xform,
                            "next_visit_date_dd", "next_visit_date_mm", "next_visit_date_yyyy",
                            is_optional=True
                            )
        if error_msg:
            return respond_to_session(router, session, error_msg,
                                      is_error=True,
                                      **{"date_name": "Next Shot Date"})

        if next_visit_date and next_visit_date < datetime.datetime.now().date():
            return respond_to_session(router, session, const.DATE_MUST_BE_IN_FUTURE,
                                      is_error=True, 
                                      **{"date_name": "Next Shot Date",
                                         "date": next_visit_date})
        syp_treatment = SyphilisTreatment(session=session,
                               date=date,
                               mother=mom,
                               shot_number=status,
                               next_visit_date=next_visit_date,
                               district=district
                               )
        syp_treatment.save()
        return respond_to_session(router, session, const.SYP_TREATMENT_COMPLETE,
                                  **{"name": name, "unique_id": unique_id})
