import datetime
from rapidsms.models import Contact
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.smgl.app import _get_value_for_command, _send_msg, get_contacttype, get_connection_from_contact, ER_TO_DRIVER, ER_TO_TRIAGE_NURSE, ER_TO_OTHER, ER_TO_CLINIC_WORKER, _generate_uid_for_er, INITIAL_AMBULANCE_RESPONSE, _get_allowed_ambulance_workflow_contact, NOT_REGISTERED_TO_CONFIRM_ER, ER_CONFIRM_SESS_NOT_FOUND, AMB_CANT_FIND_UID, AMB_OUTCOME_NO_OUTCOME, NOT_ALLOWED_ER_WORKFLOW, AMB_OUTCOME_ORIGINATING_LOCATION_INFO
from mwana.apps.smgl.models import AmbulanceRequest, PregnantMother, AmbulanceResponse, AmbulanceOutcome

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that makemessages finds
# our text.
_ = lambda s: s

AMBULANCE_WORKFLOW_SYMPTOMS = {
    #code: sympton_string
    "symptom_1": "Some symptom 1",
    "12": "Anemia",
}

def _get_symptom_from_code(xform):
    try:
        return AMBULANCE_WORKFLOW_SYMPTOMS[_get_value_for_command('danger_signs', xform)]
    except KeyError:
        return _get_value_for_command('danger_signs', xform)

def _get_receiving_facility(location):
    """
    Get the facility that should receive an emergency patient, based on the clinic they are coming from
    """
    #currently we're just directing patients to whatever is their parent location
    parent = location.parent_location
    return parent

def _pick_er_driver(session, xform):
    ad_type, error = get_contacttype(session, 'am')
    ads = Contact.objects.filter(types=ad_type)
    if ads.count():
        return ads[0]
    else:
        raise TypeError('No Ambulance Driver type found!')

def _pick_other_er_recip(session, xform):
    other_type, error = get_contacttype(session, 'dmho')
    others = Contact.objects.filter(types=other_type)
    if others.count():
        return others[0]
    else:
        raise TypeError('No Other recipient type found for Ambulance Request Workflow!')

def _pick_er_triage_nurse(session, xform):
    tn_type, error = get_contacttype(session, 'tn')
    tns = Contact.objects.filter(types=tn_type)
    if tns.count():
        return tns[0]
    else:
        raise TypeError('No Triage Nurse type found!')

def _pick_clinic_recip(session, xform):
    cw_type, error = get_contacttype(session, 'clinic-worker')
    cws = Contact.objects.filter(types=cw_type)
    if cws.count():
        return cws[0]
    else:
        raise TypeError('No clinic worker found!')

def _broadcast_to_ER_users(ambulance_session, session, xform, router, message=None):
    #Figure out who to alert
    ambulance_driver = _pick_er_driver(session, xform)
    ambulance_session.ambulance_driver = ambulance_driver
    driver_conn = get_connection_from_contact(ambulance_driver)
    if driver_conn:
        if message:
            _send_msg(driver_conn, message, router, **session.template_vars)
        else:
            _send_msg(driver_conn, ER_TO_DRIVER, router, **session.template_vars)
        ambulance_session.ad_msg_sent = True
    else:
        ambulance_session.ad_msg_sent = False

    tn = _pick_er_triage_nurse(session, xform)
    ambulance_session.triage_nurse = tn
    tn_conn = get_connection_from_contact(tn)
    if tn_conn:
        if message:
            _send_msg(tn_conn, message, router, **session.template_vars)
        else:
            _send_msg(tn_conn, ER_TO_TRIAGE_NURSE, router, **session.template_vars)
        ambulance_session.tn_msg_sent = True
    else:
        ambulance_session.tn_msg_sent = False

    other_recip = _pick_other_er_recip(session,xform)
    if other_recip: #less important, so not critical if this contact doesn't exist.
        ambulance_session.other_recipient = other_recip
        other_conn = get_connection_from_contact(other_recip)
        if other_conn:
            if message:
                _send_msg(other_conn, message, router, **session.template_vars)
            else:
                _send_msg(other_conn, ER_TO_OTHER, router, **session.template_vars)
            ambulance_session.other_msg_sent = True
        else:
            ambulance_session.other_msg_sent = False

    clinic_recip = _pick_clinic_recip(session, xform)
    if clinic_recip:
        ambulance_session.receiving_facility_recipient = clinic_recip
        clinic_conn = get_connection_from_contact(clinic_recip)
        if clinic_conn:
            if message:
                _send_msg(clinic_conn, message, router, **session.template_vars)
            else:
                _send_msg(clinic_conn, ER_TO_CLINIC_WORKER, router, **session.template_vars)
            ambulance_session.receiving_facility_recipient_sent = True
        else:
            ambulance_session.other_clinic_worker_sent = False

    ambulance_session.save()

def ambulance_request(session, xform, router):
    connection = session.connection
    unique_id = _get_value_for_command('unique_id', xform)
    danger_signs = _get_symptom_from_code(xform)

    session.template_vars.update({"sender_phone_number": connection.identity})
    amb = AmbulanceRequest()
    amb.danger_sign = danger_signs
    amb.connection = connection
    contact = None
    try:
        contact = Contact.objects.get(connection=connection)
    except ObjectDoesNotExist:
        pass
    amb.contact = contact
    if contact:
        amb.from_location = contact.location
        session.template_vars.update({"from_location": str(contact.location.name)})
    else:
        session.template_vars.update({"from_location": "UNKNOWN"})

    if not unique_id:
        unique_id = _generate_uid_for_er()

    session.template_vars.update({'unique_id': unique_id})
    amb.mother_uid = unique_id

    #try match uid to mother
    mother = None
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        pass
    amb.mother = mother
    amb.save()

    #Respond that we're on it.
    _send_msg(connection, INITIAL_AMBULANCE_RESPONSE, router, **session.template_vars)

    _broadcast_to_ER_users(amb, session, xform, router=router)


    return True

def ambulance_confirm(session, xform, router):
    connection = session.connection
    contact = _get_allowed_ambulance_workflow_contact(session)
    if not contact:
        _send_msg(connection, NOT_REGISTERED_TO_CONFIRM_ER, router, **session.template_vars)

    ambulance_response = AmbulanceResponse()

    unique_id = _get_value_for_command('unique_id', xform)
    ambulance_response.mother_uid = unique_id
    session.template_vars.update({'unique_id': unique_id})
    #try match uid to mother
    mother = None
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        pass
    ambulance_response.mother = mother

    status = _get_value_for_command('response', xform)
    ambulance_response.response = status

    #we might be dealing with a mother that has gone through ER multiple times
    ambulance_requests = AmbulanceRequest.objects.filter(mother_uid=unique_id)\
                .exclude(confirmed=True)\
                .order_by('-requested_on')
    if not ambulance_requests.count():
        _send_msg(connection, ER_CONFIRM_SESS_NOT_FOUND, router, **session.template_vars)
        return True

    ambulance_response.ambulance_request = ambulance_requests[0]

    #great we found what they're responding to.
    ambulance_request = ambulance_requests[0]
    tn_type, error = get_contacttype(session,'TN')
    amb_type, error = get_contacttype(session, 'AM')
    other_type, error = get_contacttype(session, 'DMO')
    clinic_type, error = get_contacttype(session, 'clinic-worker')
    ambulance_request.confirmed = True
    confirm_contact_type = None
    if Contact.objects.filter(connection=connection, types=tn_type).count():
        #this s a Triage Nurse
        ambulance_request.tn_confirmed_on = datetime.datetime.utcnow()
        confirm_contact_type = tn_type
    elif Contact.objects.filter(connection=connection, types=amb_type).count():
        #Ambulance (Driver) type
        ambulance_request.ad_confirmed_on = datetime.datetime.utcnow()
        confirm_contact_type = amb_type
    elif Contact.objects.filter(connection=connection, types=other_type).count():
        #other type
        ambulance_request.other_confirmed_on = datetime.datetime.utcnow()
        confirm_contact_type = other_type
    elif Contact.objects.filter(connection=connection, types=clinic_type).count():
        #Receiving Facility Clinic Worker type
        ambulance_request.receiving_facility_confirmed_on = datetime.datetime.utcnow()
        confirm_contact_type = clinic_type
    session.template_vars.update({"confirm_type": confirm_contact_type,
                                  "name": contact.name})

    _broadcast_to_ER_users(ambulance_request, session, xform,
        message=_("The Emergency Request for Mother with Unique ID: "
                  "%(unique_id)s has been marked %(status)s by %(name)s "
                  "(%(confirm_type)s)"), router=router)

    ambulance_request.save()
    ambulance_response.save()
    return True

def ambulance_outcome(session, xform, router):
    connection = session.connection
    contact = _get_allowed_ambulance_workflow_contact(session)
    if not contact:
        _send_msg(connection, NOT_ALLOWED_ER_WORKFLOW, router,
            **session.template_vars)
        return True

    unique_id = _get_value_for_command('unique_id', xform)
    outcome = _get_value_for_command('outcome', xform)
    session.template_vars.update({
        "unique_id": unique_id,
        "outcome": outcome
    })

    if not outcome:
        _send_msg(connection, AMB_OUTCOME_NO_OUTCOME, router,
            **session.template_vars)
        return True

    req = AmbulanceRequest.objects.filter(mother_uid=unique_id).order_by('-requested_on')
    if not req.count():
        _send_msg(connection, AMB_CANT_FIND_UID, router, **session.template_vars)
        return True
    req = req[0] #select latest one

    outcome = AmbulanceOutcome()
    outcome.ambulance_request = req
    outcome.mother_uid = unique_id
    outcome.outcome = outcome
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        mother = None
    outcome.mother = mother
    outcome.save()
    session.template_vars.update({"contact_type": contact.types.all()[0],
                                  "name": contact.name})
    _broadcast_to_ER_users(req,session, xform,
        message=_("A patient outcome for an Emergency Response for "
                  "Patient (%(unique_id)s) has been filed by %(name)s "
                  "(%(contact_type)s)"), router=router)
    _send_msg(req.connection, AMB_OUTCOME_ORIGINATING_LOCATION_INFO, router, **session.template_vars)
    return True
