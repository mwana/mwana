from rapidsms.messages import OutgoingMessage
from mwana.apps.smgl.app import FACILITY_NOT_RECOGNIZED
from mwana.apps.smgl.models import Referral, PregnantMother
from mwana.apps.smgl.utils import get_location, to_time, mom_or_none
from mwana.apps.smgl import const
from mwana.apps.contactsplus.models import ContactType
from rapidsms.models import Contact
from datetime import datetime

def refer(session, xform, router):
    name = session.connection.contact.name if session.connection.contact else ""
    
    mother_id = xform.xpath("form/unique_id")
    facility_id = xform.xpath("form/facility")
    loc = get_location(facility_id)
    if not loc:
        router.outgoing(OutgoingMessage(session.connection, 
                                        FACILITY_NOT_RECOGNIZED % { 
                                            "facility": facility_id
                                        }))
    else:
        referral = Referral(facility=loc, form_id=xform.get_id,
                            session=session, date=datetime.utcnow())
        referral.set_mother(mother_id)
        reasons = xform.xpath("form/reason")
        if reasons:
            for r in reasons.split(" "):
                referral.set_reason(r)
        referral.status = xform.xpath("form/status")
        try:
            referral.time = to_time(xform.xpath("form/time"))
        except ValueError, e:
            router.outgoing(OutgoingMessage(session.connection, str(e)))
            return True
        
        referral.save()
        resp = const.REFERRAL_RESPONSE % {"name": name, "unique_id": mother_id}
        router.outgoing(OutgoingMessage(session.connection, resp))
        for c in _get_people_to_notify(referral):
            if c.default_connection:
                msg = const.REFERRAL_NOTIFICATION % {"unique_id": mother_id,
                                                     "reason": ", ".join(referral.get_reasons()),
                                                     "time": referral.time.strftime("%H:%M")}
                router.outgoing(OutgoingMessage(c.default_connection, msg))
    return True

def referral_outcome(session, xform, router):
    name = session.connection.contact.name if session.connection.contact else ""
    mother_id = xform.xpath("form/unique_id")
    
    refs = Referral.objects.filter(mother_uid=mother_id.lower()).order_by('-date')
    if not refs.count():
        router.outgoing(OutgoingMessage(session.connection, 
                                        const.REFERRAL_NOT_FOUND % \
                                        {"unique_id": mother_id}))
        return True
    
    ref = refs[0]
    if ref.responded:
        router.outgoing(OutgoingMessage(session.connection, 
                                        const.REFERRAL_ALREADY_RESPONDED % \
                                        {"unique_id": mother_id}))
        return True
    
    ref.responded = True
    if xform.xpath("form/mother_outcome").lower() == const.REFERRAL_OUTCOME_NOSHOW:
        ref.mother_showed = False
    else:
        ref.mother_showed = True
        ref.mother_outcome = xform.xpath("form/mother_outcome")
        ref.baby_outcome = xform.xpath("form/baby_outcome")
        ref.mode_of_delivery = xform.xpath("form/mode_of_delivery")
        
    ref.save()
    router.outgoing(OutgoingMessage(session.connection, 
                                    const.REFERRAL_OUTCOME_RESPONSE % \
                                        {'name': name, "unique_id": mother_id}))
    return True

def _get_people_to_notify(referral):
    types = ContactType.objects.filter\
        (slug__in=[const.CTYPE_DATACLERK,
                   const.CTYPE_TRIAGENURSE]).all()
    return Contact.objects.filter(types__in=types, location=referral.facility)