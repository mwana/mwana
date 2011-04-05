# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
from mwana.apps.labresults.handlers.join import JoinHandler
from mwana.apps.labresults.models import Result

RESULTS_READY     = "Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your pin code to retrieve these results."
NO_RESULTS        = "Hello %(name)s. There are no new DBS test results for %(clinic)s right now. We'll let you know as soon as more results are available."
BAD_PIN           = "Sorry, that was not the correct pin code. Your pin code is a 4-digit number like 1234. If you forgot your pin code, reply with keyword 'HELP'"
SELF_COLLECTED    = "Hi %(name)s. It looks like you already collected your DBS results. To check for new results reply with keyword 'CHECK'"
ALREADY_COLLECTED = "Hi %(name)s. It looks like the results you are looking for were already collected by %(collector)s. To check for new results reply with keyword 'CHECK'"
RESULTS           = "Thank you! Here are your results: "
RESULTS_PROCESSED = "%(name)s has collected these results"
INSTRUCTIONS      = "Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!"
NOT_REGISTERED    = "Sorry you must be registered with a clinic to check results. " + JoinHandler.HELP_TEXT
DEMO_FAIL         = "Sorry you must be registered with a clinic or specify in your message to initiate a demo of Results160. To specify a clinic send: DEMO <CLINIC_CODE>"
HUB_DEMO_FAIL     = "Sorry you must be registered with a location or specify in your message to initiate a reports demo. To specify a location send: HUBDEMO <LOCATION_CODE>"
PRINTER_RESULTS   = "%(clinic)s.\r\nPatient ID: %(req_id)s.\r\n%(test_type)s:\r\n%(result)s.\r\nApproved by %(lab_name)s."
CHANGED_PRINTER_RESULTS   = "%(clinic)s.\r\nPatient ID: %(req_id)s.\r\n%(test_type)s:\r\n%(result)s.\r\nApproved by %(lab_name)s."

TEST_TYPE = "HIV-DNAPCR Result"
ADH_LAB_NAME = "ADH DNA-PCR LAB"
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

def build_printer_results_messages(results):
    """
    From a list of lab results, build a list of messages reporting 
    their status
    """
    result_strings = []
    # if messages are updates to requisition ids
    for res in results:
        if urgent_requisitionid_update(res):
            msg = (settings.CHANGED_PRINTER_RESULTS % {"clinic":res.clinic.name,
                   "old_req_id":res.old_value.split(":")[0],
                   "old_result":res.get_old_result_text(),
                   "new_req_id":res.requisition_id,
                   "new_result":res.get_result_text(),
                   "test_type":TEST_TYPE,
                   "lab_name":settings.ADH_LAB_NAME})
        else:
            msg = (settings.PRINTER_RESULTS % {"clinic":res.clinic.name,
                   "req_id":res.requisition_id,
                   "result":res.get_result_text(),
                   "test_type":TEST_TYPE,
                   "lab_name":settings.ADH_LAB_NAME})
        result_strings.append(msg)
               
    return result_strings

def build_results_messages(results):
    """
    From a list of lab results, build a list of messages reporting
    their status
    """
    result_strings = []
    max_len = settings.MAX_SMS_LENGTH
    # if messages are updates to requisition ids
    for res in results:
        if urgent_requisitionid_update(res):
            result_strings.append("**** %s;%s changed to %s;%s" % (
                                  res.old_value.split(":")[0],
                                  res.get_old_result_text(),
                                  res.requisition_id,
                                  res.get_result_text()))
        else:
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
 
