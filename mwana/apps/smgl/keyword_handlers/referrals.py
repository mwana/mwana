import logging

from rapidsms.messages import OutgoingMessage
from mwana.apps.smgl.models import Referral, AmbulanceRequest, AmbulanceResponse
from mwana.apps.smgl.utils import get_location, to_time, get_session_message
from mwana.apps.smgl import const
from mwana.apps.contactsplus.models import ContactType
from rapidsms.models import Contact
from datetime import datetime
from mwana.apps.smgl.decorators import registration_required, is_active
from django.template.defaultfilters import yesno

from mwana.apps.smgl.app import (get_value_from_form, send_msg, ER_TO_DRIVER,
    ER_TO_TRIAGE_NURSE, ER_STATUS_UPDATE,
    INITIAL_AMBULANCE_RESPONSE, _get_allowed_ambulance_workflow_contact,
    NOT_REGISTERED_TO_CONFIRM_ER, ER_CONFIRM_SESS_NOT_FOUND, ER_TO_CLINIC_WORKER,
    AMB_OUTCOME_ORIGINATING_LOCATION_INFO, AMB_OUTCOME_FILED, FACILITY_NOT_RECOGNIZED,
    AMB_RESPONSE_ORIGINATING_LOCATION_INFO, AMB_RESPONSE_NOT_AVAILABLE)

logger = logging.getLogger(__name__)
# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s


@registration_required
@is_active
def refer(session, xform, router):
    assert session.connection.contact is not None, \
        "Must be a registered contact to refer"
    assert session.connection.contact.location is not None, \
        "Contact must have a location to refer"
    get_session_message(session)
    contact = session.connection.contact
    name = contact.name

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
        referral.from_facility = session.connection.contact.location
        try:
            referral.time = to_time(xform.xpath("form/time"))
        except ValueError, e:
            router.outgoing(OutgoingMessage(session.connection, str(e)))
            get_session_message(session, direction='O')
            return True

        status = xform.xpath("form/status")
        referral.status = status
        referral.save()
        if referral.status == 'em':
            # Generate an Ambulance Request
            session.template_vars.update({"sender_phone_number": session.connection.identity})
            amb = AmbulanceRequest()
            amb.session = session
            session.template_vars.update({"from_location": str(referral.from_facility.name)})
            amb.set_mother(mother_id)
            amb.save()
            referral.amb_req = amb
            referral.save()
            #Respond that we're on it.
            send_msg(session.connection, INITIAL_AMBULANCE_RESPONSE, router, **session.template_vars)
            _broadcast_to_ER_users(amb, session, xform, router=router)
        else:
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
    get_session_message(session, direction='O')
    return True


@registration_required
@is_active
def referral_outcome(session, xform, router):
    get_session_message(session)
    contact = session.connection.contact
    name = contact.name
    mother_id = xform.xpath("form/unique_id")

    refs = Referral.objects.filter(mother_uid=mother_id.lower()).order_by('-date')
    if not refs.count():
        router.outgoing(OutgoingMessage(session.connection,
                                        const.REFERRAL_NOT_FOUND % \
                                        {"unique_id": mother_id}))
        get_session_message(session, direction='O')
        return True

    ref = refs[0]
    if ref.responded:
        router.outgoing(OutgoingMessage(session.connection,
                                        const.REFERRAL_ALREADY_RESPONDED % \
                                        {"unique_id": mother_id}))
        get_session_message(session, direction='O')
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

    if ref.amb_req:
        if ref.amb_req.ambulanceresponse_set.all().order_by('-responded_on')[0].response != 'na':
            session.template_vars.update({"contact_type": contact.types.all()[0],
                                          "name": contact.name})

            if xform.xpath("form/mode_of_delivery") == 'noamb':
                _broadcast_to_ER_users(ref.amb_req, session, xform,
                                       message=_(AMB_OUTCOME_FILED), router=router)
            send_msg(ref.session.connection, AMB_OUTCOME_ORIGINATING_LOCATION_INFO, router, **session.template_vars)
            get_session_message(session, direction='O')
            return True
    else:
        router.outgoing(OutgoingMessage(session.connection,
                                        const.REFERRAL_OUTCOME_RESPONSE % \
                                            {'name': name, "unique_id": mother_id}))
        get_session_message(session, direction='O')

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


@registration_required
@is_active
def emergency_response(session, xform, router):
    """
    This handler deals with a status update from an ER Driver or Triage Nurse
    about a specific ambulance

    i.e. Ambulance on the way/delayed/not available
    """
    logger.debug('POST PROCESSING FOR RESP KEYWORD')
    connection = session.connection
    contact = _get_allowed_ambulance_workflow_contact(session)
    if not contact:
        send_msg(connection, NOT_REGISTERED_TO_CONFIRM_ER, router, **session.template_vars)
        return True

    ambulance_response = AmbulanceResponse()
    ambulance_response.responder = contact
    ambulance_response.session = session

    unique_id = get_value_from_form('unique_id', xform)
    ambulance_response.mother_uid = unique_id
    session.template_vars.update({'unique_id': unique_id})
    #try match uid to mother
    ambulance_response.set_mother(unique_id)
    ambulance_response.mother_uid = unique_id

    status = get_value_from_form('status', xform).lower()
    ambulance_response.response = status
    session.template_vars.update({"status": status.upper(),
                                   "response": status.upper()})

    #we might be dealing with a mother that has gone through ER multiple times
    ambulance_requests = AmbulanceRequest.objects.filter(mother_uid=unique_id)\
                .exclude(referral__responded=True)\
                .order_by('-id')
    if not ambulance_requests.count():
        #session doesn't exist or it has already been confirmed
        send_msg(connection, ER_CONFIRM_SESS_NOT_FOUND, router, **session.template_vars)
        return True

    #take the latest one in case this mother has been ER'd a bunch
    ambulance_response.ambulance_request = ambulance_request = ambulance_requests[0]
    ambulance_request.received_response = True

    confirm_contact_type = contact.types.all()[0]
    session.template_vars.update({"confirm_type": confirm_contact_type,
                                  "name": contact.name})

    _broadcast_to_ER_users(ambulance_request, session, xform,
        message=_(ER_STATUS_UPDATE), router=router)

    ambulance_request.save()
    ambulance_response.save()
    ref = ambulance_request.referral_set.all()[0]
    referrer_cnx = ref.session.connection
    send_msg(referrer_cnx,
             AMB_RESPONSE_ORIGINATING_LOCATION_INFO,
             router, **session.template_vars)
    if status == 'na':
        session.template_vars.update({"sender_phone_number": referrer_cnx.identity,
                                      "from_location": str(ref.from_facility.name)})
        for su in _pick_superusers(session, xform, ref.facility):
            send_msg(su.default_connection, AMB_RESPONSE_NOT_AVAILABLE, router, **session.template_vars)
    else:
        clinic_recip = _pick_clinic_recip(session, xform, ref.facility)
        if clinic_recip:
            if clinic_recip.default_connection:
                send_msg(clinic_recip.default_connection, ER_TO_CLINIC_WORKER, router, **session.template_vars)
            else:
                logger.error('No Receiving Clinic Worker found (or missing connection for Ambulance Session: %s, XForm Session: %s, XForm: %s' % (ambulance_response, session, xform))
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


def _pick_er_driver(session, xform, receiving_facility):
    ad_type = ContactType.objects.get(slug__iexact='am')
    ads = Contact.objects.filter(types=ad_type, location=receiving_facility)
    if ads.count():
        return ads[0]
    else:
        raise Exception('No Ambulance Driver type found!')


def _pick_er_triage_nurse(session, xform, receiving_facility):
    tn_type = ContactType.objects.get(slug__iexact='tn')
    tns = Contact.objects.filter(types=tn_type, location=receiving_facility)
    if tns.count():
        return tns[0]
    else:
        raise Exception('No Triage Nurse type found!')


def _pick_clinic_recip(session, xform, receiving_facility):
    cw_type = ContactType.objects.get(slug__iexact='worker')
    cws = Contact.objects.filter(types=cw_type, location=receiving_facility)
    if cws.count():
        return cws[0]
    else:
        logger.error('No clinic worker found!')


def _pick_superusers(session, xform, receiving_facility):
    superusers = Contact.objects.filter(is_super_user=True,
                                        location=receiving_facility)
    if superusers.count():
        return superusers
    else:
        raise Exception('No Ambulance Driver type found!')


def _broadcast_to_ER_users(ambulance_session, session, xform, router, message=None):
    """
    Broadcasts a message to the Emergency Response users.  If message is not
    specified, will send the default initial ER message to each respondent.
    """
    ref = ambulance_session.referral_set.all()[0]
    receiving_facility = ref.facility
    ambulance_driver = _pick_er_driver(session, xform, receiving_facility)
    ambulance_session.ambulance_driver = ambulance_driver
    if ambulance_driver.default_connection:
        if message:
            send_msg(ambulance_driver.default_connection, message, router, **session.template_vars)
        else:
            send_msg(ambulance_driver.default_connection, ER_TO_DRIVER, router, **session.template_vars)
    else:
        logger.error('No Ambulance Driver found (or missing connection) for Ambulance Session: %s, XForm Session: %s, XForm: %s' % (ambulance_session, session, xform))

    tn = _pick_er_triage_nurse(session, xform, receiving_facility)
    ambulance_session.triage_nurse = tn

    if tn.default_connection:
        if message:
            send_msg(tn.default_connection, message, router, **session.template_vars)
        else:
            send_msg(tn.default_connection, ER_TO_TRIAGE_NURSE, router, **session.template_vars)
    else:
        logger.error('No Triage Nurse found (or missing connection) for Ambulance Session: %s, XForm Session: %s, XForm: %s' % (ambulance_session, session, xform))

    ambulance_session.save()
