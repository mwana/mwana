import datetime
from rapidsms.models import Contact
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.smgl.app import _get_value_for_command, _generate_uid_for_er, ER_TO_OTHER, _send_msg, get_connection_from_contact, _pick_other_er_recip, ER_TO_TRIAGE_NURSE, _pick_er_triage_nurse, ER_TO_DRIVER, _pick_er_driver, INITIAL_AMBULANCE_RESPONSE, get_contacttype, ER_CONFIRM_SESS_NOT_FOUND, NOT_REGISTERED_TO_CONFIRM_ER, _get_allowed_ambulance_workflow_contact, THANKS_ER_CONFIRM, NOT_ALLOWED_ER_WORKFLOW, AMB_CANT_FIND_UID, AMB_RESPONSE_ORIGINATING_LOCATION_INFO, AMB_RESPONSE_THANKS, AMB_OUTCOME_ORIGINATING_LOCATION_INFO, AMB_OUTCOME_MSG_RECEIVED, AMB_OUTCOME_NO_OUTCOME
from mwana.apps.smgl.models import AmbulanceRequest, PregnantMother, AmbulanceResponse, AmbulanceOutcome

AMBULANCE_WORKFLOW_SYMPTOMS = {
    #code: sympton_string
    "symptom_1": "Some symptom 1"
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



def ambulance_request(session, xform):
    connection = session.connection
    unique_id = _get_value_for_command('unique_id', xform)
    danger_signs = _get_symptom_from_code(xform)

    session.template_vars.update({"sender_phone_number": connection.identity})
    amb = AmbulanceRequest()
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
    _send_msg(connection, INITIAL_AMBULANCE_RESPONSE, **session.template_vars)

    #Figure out who to alert
    ambulance_driver = _pick_er_driver(session, xform)
    amb.ambulance_driver = ambulance_driver
    driver_conn = get_connection_from_contact(ambulance_driver)
    if driver_conn:
        _send_msg(driver_conn, ER_TO_DRIVER, **session.template_vars)
        amb.ad_msg_sent = True
    else:
        amb.ad_msg_sent = False

    tn = _pick_er_triage_nurse(session, xform)
    amb.triage_nurse = tn
    tn_conn = get_connection_from_contact(tn)
    if tn_conn:
        _send_msg(tn_conn, ER_TO_TRIAGE_NURSE, **session.template_vars)
        amb.tn_msg_sent = True
    else:
        amb.tn_msg_sent = False

    other_recip = _pick_other_er_recip(session,xform)
    if other_recip: #less important, so not critical if this contact doesn't exist.
        amb.other_recipient = other_recip
        other_conn = get_connection_from_contact(other_recip)
        if other_conn:
            _send_msg(other_conn, ER_TO_OTHER, **session.template_vars)
            amb.other_msg_sent = True
        else:
            amb.other_msg_sent = False

    amb.save()

    return True

def ambulance_confirm(session, xform):
    connection = session.connection
    contact = _get_allowed_ambulance_workflow_contact(session)
    if not contact:
        _send_msg(connection, NOT_REGISTERED_TO_CONFIRM_ER, **session.template_vars)

    unique_id = _get_value_for_command('unique_id', xform)
    session.template_vars.update({'unique_id': unique_id})

    #we might be dealing with a mother that has gone through ER multiple times
    responses = AmbulanceRequest.objects.filter(mother_uid=unique_id).order_by('-requested_on')
    if not responses.count():
        _send_msg(connection, ER_CONFIRM_SESS_NOT_FOUND, **session.template_vars)
        return True

    #great we found what they're responding to.
    response = responses[0]
    tn_type, error = get_contacttype(session,'TN')
    amb_type, error = get_contacttype(session, 'AM')
    other_type, error = get_contacttype(session, 'DMO')

    if Contact.objects.filter(connection=connection, types=tn_type).count():
        #this s a Triage Nurse
        response.tn_confirmed = True
        response.tn_confirmed_on = datetime.datetime.utcnow()
    elif Contact.objects.filter(connection=connection, types=amb_type).count():
        #Ambulance (Driver) type
        response.ad_confirmed = True
        response.ad_confirmed_on = datetime.datetime.utcnow()
    elif Contact.objects.filter(connection=connection, types=other_type).count():
        #other type
        response.other_confirmed = True
        response.other_confirmed_on = datetime.datetime.utcnow()
    else:
        #We really shouldn't be here at this point
        pass

    response.save()

    _send_msg(connection, THANKS_ER_CONFIRM, **session.template_vars)
    return True

def ambulance_response(session, xform):
    connection = session.connection
    contact = _get_allowed_ambulance_workflow_contact(session)
    if not contact:
        _send_msg(connection, NOT_ALLOWED_ER_WORKFLOW, **session.template_vars)
        return True

    resp = AmbulanceResponse()
    unique_id = _get_value_for_command('unique_id', xform)
    session.template_vars.update({"unique_id": unique_id})
    try:
        mother = PregnantMother.objects.get(uid=unique_id)
    except ObjectDoesNotExist:
        mother = None
    resp.mother_uid = unique_id
    resp.mother = mother

    try:
        req = AmbulanceRequest.objects.get(mother_uid=unique_id)
    except ObjectDoesNotExist:
        #Abort here and notify this connection that we can't find a matching UID
        _send_msg(connection, AMB_CANT_FIND_UID, **session.template_vars)
        return True

    resp.ambulance_request = req
    resp.response = _get_value_for_command('response', xform)
    resp.save()
    session.template_vars.update({"response":resp.response})
    _send_msg(connection, AMB_RESPONSE_THANKS, **session.template_vars)
    _send_msg(req.connection, AMB_RESPONSE_ORIGINATING_LOCATION_INFO, **session.template_vars)
    return True

def ambulance_outcome(session, xform):
    connection = session.connection
    contact = _get_allowed_ambulance_workflow_contact(session)
    if not contact:
        _send_msg(connection, NOT_ALLOWED_ER_WORKFLOW, **session.template_vars)
        return True

    unique_id = _get_value_for_command('unique_id', xform)
    outcome = _get_value_for_command('outcome', xform)
    session.template_vars.update({
        "unique_id": unique_id,
        "outcome": outcome
    })
    try:
        req = AmbulanceRequest.objects.get(mother_uid=unique_id)
    except ObjectDoesNotExist:
        _send_msg(connection, AMB_CANT_FIND_UID, **session.template_vars)
        return True

    if not outcome:
        _send_msg(connection, AMB_OUTCOME_NO_OUTCOME, **session.template_vars)
        return True

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

    _send_msg(connection, AMB_OUTCOME_MSG_RECEIVED, **session.template_vars)
    _send_msg(req.connection, AMB_OUTCOME_ORIGINATING_LOCATION_INFO, **session.template_vars)
    return True
