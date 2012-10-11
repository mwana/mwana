from rapidsms.messages import OutgoingMessage
from mwana.apps.smgl.app import FACILITY_NOT_RECOGNIZED
from mwana.apps.smgl.models import Referral
from mwana.apps.smgl.utils import get_location, to_time
from mwana.apps.smgl import const
from mwana.apps.contactsplus.models import ContactType
from rapidsms.models import Contact
from datetime import datetime
from mwana.apps.smgl.decorators import registration_required
from django.template.defaultfilters import yesno


@registration_required
def refer(session, xform, router):
    assert session.connection.contact is not None, \
        "Must be a registered contact to refer"
    assert session.connection.contact.location is not None, \
        "Contact must have a location to refer"
    name = session.connection.contact.name

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

        referral.from_facility = session.connection.contact.location
        referral.save()
        resp = const.REFERRAL_RESPONSE % {"name": name, "unique_id": mother_id}
        router.outgoing(OutgoingMessage(session.connection, resp))
        from_facility = session.connection.contact.location.name
        for c in _get_people_to_notify(referral):
            if c.default_connection:
                verbose_reasons = [Referral.REFERRAL_REASONS[r] for r in referral.get_reasons()]
                msg = const.REFERRAL_NOTIFICATION % {"unique_id": mother_id,
                                                     "facility": from_facility,
                                                     "reason": ", ".join(verbose_reasons),
                                                     "time": referral.time.strftime("%H:%M"),
                                                     "is_emergency": yesno(referral.is_emergency)}
                router.outgoing(OutgoingMessage(c.default_connection, msg))
    return True


@registration_required
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

    # also notify folks at the referring facility about the outcome
    for c in _get_people_to_notify_outcome(ref):
        if c.default_connection:
            if ref.mother_showed:
                router.outgoing(OutgoingMessage(c.default_connection,
                                                const.REFERRAL_OUTCOME_NOTIFICATION % \
                                                    {"unique_id": ref.mother_uid,
                                                     "date": ref.date.date(),
                                                     "mother_outcome": ref.get_mother_outcome_display(),
                                                     "baby_outcome": ref.get_baby_outcome_display(),
                                                     "delivery_mode": ref.get_mode_of_delivery_display()}))
            else:
                router.outgoing(OutgoingMessage(c.default_connection,
                                                const.REFERRAL_OUTCOME_NOTIFICATION_NOSHOW % \
                                                    {"unique_id": ref.mother_uid,
                                                     "date": ref.date.date()}))
    return True


def _get_people_to_notify(referral):
    # who to notifiy on an initial referral
    # this should be the people who are being referred to
    types = ContactType.objects.filter(
                    slug__in=[const.CTYPE_DATACLERK, const.CTYPE_TRIAGENURSE]
                ).all()
    return Contact.objects.filter(types__in=types, location=referral.facility)


def _get_people_to_notify_outcome(referral):
    # who to notifiy when we've collected a referral outcome
    # this should be the people who made the referral
    # (more specifically, the person who sent it in + all
    # data clerks and in-charges at their facility)
    types = ContactType.objects.filter(
                slug__in=[const.CTYPE_DATACLERK, const.CTYPE_INCHARGE]
                ).all()
    from_facility = referral.referring_facility
    facility_contacts = list(Contact.objects.filter(
                types__in=types,
                location=from_facility)
            ) if from_facility else []
    if referral.get_connection().contact and \
       referral.get_connection().contact not in facility_contacts:
        facility_contacts.append(referral.get_connection().contact)
    return facility_contacts
