import logging

from rapidsms.messages import OutgoingMessage
from mwana.apps.smgl.models import Referral, AmbulanceRequest, AmbulanceResponse
from mwana.apps.smgl.utils import get_location, to_time, respond_to_session
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
    AMB_RESPONSE_ORIGINATING_LOCATION_INFO, AMB_RESPONSE_NOT_AVAILABLE,
    AMB_RESPONSE_ALREADY_HANDLED)

logger = logging.getLogger(__name__)
# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s


@registration_required
@is_active
def refer(session, xform, router):
    """
    Handler for REF keyword

    Used to record a referral to another location

    Format:
    REFER Mother_UID receiving_facility_id Reason TIME EM/NEM
    """

    assert session.connection.contact is not None, \
        "Must be a registered contact to refer"
    assert session.connection.contact.location is not None, \
        "Contact must have a location to refer"
    contact = session.connection.contact
    name = contact.name

    mother_id = xform.xpath("form/unique_id")
    facility_id = xform.xpath("form/facility")
    loc = get_location(facility_id)
    if not loc:
        return respond_to_session(router, session, FACILITY_NOT_RECOGNIZED,
                                  is_error=True,
                                  **{"facility": facility_id})
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
            return respond_to_session(router, session, str(e), 
                                      is_error=True)

        status = xform.xpath("form/status")
        referral.status = status
        referral.save()
        # IF CBA, DO NOT SEND AN EMERGENCY REQUEST, JUST NOTIFY via _get_people_to_notify
        is_cba = ['cba'] == list(contact.types.all().values_list('slug', flat=True))
        if is_cba or referral.status == 'nem':
            loc = session.connection.contact.location
            from_facility = loc.name if not loc.parent else "%s (in %s)" % \
                (loc.name, loc.parent.name)
            for c in _get_people_to_notify(referral):
                if c.default_connection:
                    verbose_reasons = [Referral.REFERRAL_REASONS[r] for r in referral.get_reasons()]
                    msg = const.REFERRAL_NOTIFICATION % {"unique_id": mother_id,
                                                         "facility": from_facility,
                                                         "reason": ", ".join(verbose_reasons),
                                                         "time": referral.time.strftime("%H:%M"),
                                                         "is_emergency": yesno(referral.is_emergency)}
                    router.outgoing(OutgoingMessage(c.default_connection, msg))
            return respond_to_session(router, session, const.REFERRAL_RESPONSE,
                                      name=name, unique_id=mother_id)
        else:
            # Generate an Ambulance Request
            session.template_vars.update({"sender_phone_number": session.connection.identity})
            amb = AmbulanceRequest()
            amb.session = session
            session.template_vars.update({"from_location": str(referral.from_facility.name)})
            amb.set_mother(mother_id)
            amb.save()
            referral.amb_req = amb
            referral.save()
            _broadcast_to_ER_users(amb, session, xform, router=router)
            # Respond that we're on it.
            return respond_to_session(router, session, INITIAL_AMBULANCE_RESPONSE)

@registration_required
@is_active
def referral_outcome(session, xform, router):
    contact = session.connection.contact
    name = contact.name
    mother_id = xform.xpath("form/unique_id")

    refs = Referral.objects.filter(mother_uid=mother_id.lower()).order_by('-date')
    if not refs.count():
        return respond_to_session(router, session, const.REFERRAL_NOT_FOUND,
                                  is_error=True, **{"unique_id": mother_id})

    ref = refs[0]
    if ref.responded:
        return respond_to_session(router, session, const.REFERRAL_ALREADY_RESPONDED,
                                  is_error=True, **{"unique_id": mother_id})

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
            return respond_to_session(router, session, AMB_OUTCOME_ORIGINATING_LOCATION_INFO,
                                      **session.template_vars)
    else:
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

        return respond_to_session(router, session, const.REFERRAL_OUTCOME_RESPONSE,
                                  **{'name': name, "unique_id": mother_id})

@registration_required
@is_active
def emergency_response(session, xform, router):
    """
    This handler deals with a status update from an ER Driver or Triage Nurse
    about a specific ambulance

    i.e. Ambulance on the way/delayed/not available
    """
    logger.debug('POST PROCESSING FOR RESP KEYWORD')
    contact = _get_allowed_ambulance_workflow_contact(session)
    if not contact:
        return respond_to_session(router, session, NOT_REGISTERED_TO_CONFIRM_ER,
                                  is_error=True)

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
        return respond_to_session(router, session, ER_CONFIRM_SESS_NOT_FOUND,
                                  is_error=True, **{'unique_id': unique_id})

    #take the latest one in case this mother has been ER'd a bunch
    ambulance_response.ambulance_request = ambulance_request = ambulance_requests[0]
    if ambulance_request.ambulanceresponse_set.filter(response='otw').exists():
        # if we've already responded 'otw' then just respond indicating such
        last_response = ambulance_request.ambulanceresponse_set.filter(response='otw')[0]
        return respond_to_session(router, session, AMB_RESPONSE_ALREADY_HANDLED,
                                  response=last_response.response,
                                  person=last_response.responder)

    ambulance_request.received_response = True # FIXME: this dosen't do anything?

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
        try:
            help_admins = _pick_help_admin(session, xform, ref.facility)
        except Exception:
            logger.error('No Help Admin found (or missing connection for Ambulance Session: %s, XForm Session: %s, XForm: %s' % (ambulance_response, session, xform))
        else:
            for ha in help_admins:
                send_msg(ha.default_connection, AMB_RESPONSE_NOT_AVAILABLE, router, **session.template_vars)
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
    loc_parent = referral.from_facility.parent if referral.from_facility else None
    facility_lookup = loc_parent or referral.facility
    return Contact.objects.filter(types__in=types,
                                  location=facility_lookup,
                                  is_active=True)


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
                location=from_facility,
                is_active=True)
            ) if from_facility else []
    contact = referral.get_connection().contact
    if contact and contact.is_active and contact not in facility_contacts:
        facility_contacts.append(referral.get_connection().contact)
    return facility_contacts


def _pick_er_driver(session, xform, receiving_facility):
    ad_type = ContactType.objects.get(slug__iexact='am')
    ads = Contact.objects.filter(types=ad_type,
                                 location=receiving_facility,
                                 is_active=True)
    if ads.count():
        return ads[0]
    else:
        raise Exception('No Ambulance Driver type found!')


def _pick_er_triage_nurse(session, xform, receiving_facility):
    tn_type = ContactType.objects.get(slug__iexact='tn')
    tns = Contact.objects.filter(types=tn_type,
                                 location=receiving_facility,
                                 is_active=True)
    if tns.count():
        return tns[0]
    else:
        raise Exception('No Triage Nurse type found!')


def _pick_clinic_recip(session, xform, receiving_facility):
    cw_type = ContactType.objects.get(slug__iexact=const.CTYPE_CLINICWORKER)
    cws = Contact.objects.filter(types=cw_type,
                                 location=receiving_facility,
                                 is_active=True)
    if cws.count():
        return cws[0]
    else:
        logger.error('No clinic worker found!')


def _pick_help_admin(session, xform, receiving_facility):
    help_admins = Contact.objects.filter(is_help_admin=True,
                                        location=receiving_facility,
                                        is_active=True)
    if help_admins.count():
        return help_admins
    else:
        raise Exception('No Help Admin type found!')


def _broadcast_to_ER_users(ambulance_session, session, xform, router, message=None):
    """
    Broadcasts a message to the Emergency Response users.  If message is not
    specified, will send the default initial ER message to each respondent.
    """
    ref = ambulance_session.referral_set.all()[0]
    receiving_facility = ref.facility
    try:
        ambulance_driver = _pick_er_driver(session, xform, receiving_facility)
    except Exception:
        logger.error('No Ambulance Driver found (or missing connection) for Ambulance Session: %s, XForm Session: %s, XForm: %s' % (ambulance_session, session, xform))
    else:
        ambulance_session.ambulance_driver = ambulance_driver
        if ambulance_driver.default_connection:
            if message:
                send_msg(ambulance_driver.default_connection, message, router, **session.template_vars)
            else:
                send_msg(ambulance_driver.default_connection, ER_TO_DRIVER, router, **session.template_vars)

    try:
        tn = _pick_er_triage_nurse(session, xform, receiving_facility)
    except Exception:
        logger.error('No Triage Nurse found (or missing connection) for Ambulance Session: %s, XForm Session: %s, XForm: %s' % (ambulance_session, session, xform))
    else:
        ambulance_session.triage_nurse = tn
        if tn.default_connection:
            if message:
                send_msg(tn.default_connection, message, router, **session.template_vars)
            else:
                send_msg(tn.default_connection, ER_TO_TRIAGE_NURSE, router, **session.template_vars)

    ambulance_session.save()
