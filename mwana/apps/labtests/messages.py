# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from django.conf import settings
from mwana.apps.labresults.handlers.join import JoinHandler
_ = lambda s: s

RESULTS_READY     = "Hello %(name)s. We have %(count)s %(test_type)s test results ready for you. Please reply to this SMS with your pin code to retrieve these results."
PARTICIPANT_RESULTS_READY = "Your appointment is due at %(clinic)s. Bring your referral letter with you to this appointment. If you got this msg by mistake please ignore"
NO_RESULTS        = "Hello %(name)s. There are no new test results for %(clinic)s right now. We'll let you know as soon as more results are available."
BAD_PIN           = "Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'"
SELF_COLLECTED    = "Hi %(name)s. It looks like you already collected your viral load results. To check for new results reply with keyword 'VL'"
ALREADY_COLLECTED = "Hi %(name)s. It looks like the results you are looking for were already collected by %(collector)s. To check for new results reply with keyword 'VL'"
RESULTS           = "Thank you! Here are your results: "
RESULTS_PROCESSED = "%(name)s has collected these results"
INSTRUCTIONS      = "Please record these results in your clinic records and promptly delete them from your phone. Thank you again %(name)s!"
NOT_REGISTERED    = "Sorry you must be registered with a clinic to check results. " + JoinHandler.HELP_TEXT
CLINIC_DEFAULT_RESPONSE = "Invalid Keyword. Valid keywords are CHECK, RESULT, SENT, TRACE, MSG CBA, MSG CLINIC,VL, MSG ALL and MSG DHO. Respond with any keyword or HELP for more information"
UNREGISTERED_DEFAULT_RESPONSE = _("Invalid Keyword. Please send the keyword HELP if you need to be assisted.")

TEST_TYPE = "Viral Load Result"


def urgent_requisitionid_update(result):
    """
    Returns True if there has been a critical update in requisition id. That is
    if a result had a req_id for another person.
    """
    toreturn = False
    if result.record_change:
        if result.record_change in ['req_id', 'both']:
            toreturn = True
    return toreturn


def get_lab_name(result):
    labs = settings

    if result.payload:
        return labs.get(result.payload.source, settings.ADH_LAB_NAME)
    else:
        return settings.ADH_LAB_NAME


def build_results_messages(results):
    """
    From a list of lab results, build a list of messages reporting
    their status
    """
    result_strings = []
    max_len = settings.MAX_SMS_LENGTH
    # if messages are updates to requisition ids
    for res in results:
        result_strings.append("**** %s;%s" % (res.requisition_id,
                                              res.get_result_text()))

    result_text, remainder = combine_to_length(result_strings,
                                               length=max_len-len(RESULTS))
    first_msg = RESULTS + result_text
    responses = [first_msg]
    while remainder:
        next_msg, remainder = combine_to_length(remainder)
        responses.append(next_msg)
    return responses


def combine_to_length(list, delimiter=". ", length=None):
    """
    Combine a list of strings to a maximum of a specified length, using the 
    delimiter to separate them.  Returns the combined strings and the 
    remainder as a tuple.
    """
    if length is None:
        length = settings.MAX_SMS_LENGTH
    if not list:  return ("", [])
    if len(list[0]) > length:
        raise Exception("None of the messages will fit in the specified length of %s" % length)

    msg = ""
    for i in range(len(list)):
        item = list[i]
        new_msg = item if not msg else msg + delimiter + item
        if len(new_msg) <= length:
            msg = new_msg
        else:
            return (msg, list[i:])
    return (msg, [])
