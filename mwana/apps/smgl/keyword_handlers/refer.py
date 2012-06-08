from rapidsms.messages import OutgoingMessage
from mwana.apps.smgl.app import REFERRAL_RESPONSE, get_location,\
    FACILITY_NOT_RECOGNIZED
from mwana.apps.smgl.models import Referral

def refer(session, xform, router):
    name = session.connection.contact.name if session.connection.contact else ""
    
    mother_id = xform.xpath("form/unique_id")
    facility_id = xform.xpath("form/facility")
    loc = get_location(session, facility_id)
    if not loc:
        router.outgoing(OutgoingMessage(session.connection, 
                                        FACILITY_NOT_RECOGNIZED % { 
                                            "facility": facility_id
                                        }))
    else:
        referral = Referral(facility=loc, form_id=xform.get_id,
                            session=session)
        referral.set_mother(mother_id)
        referral.save()
        resp = REFERRAL_RESPONSE % {"name": name, "unique_id": mother_id}
        router.outgoing(OutgoingMessage(session.connection, resp))
    return True