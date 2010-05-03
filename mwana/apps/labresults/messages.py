from mwana.apps.labresults.handlers.register import RegisterHandler

RESULTS_READY     = "Hello %(name)s. We have %(count)s DBS test results ready for you. Please reply to this SMS with your security code to retrieve these results."
NO_RESULTS        = "Hello %(name)s. There are no new DBS test results for %(clinic)s right now. We'll let you know as soon as more results are available."
BAD_PIN           = "Sorry, that was not the correct security code. Your security code is a 4-digit number like 1234. If you forgot your security code, reply with keyword 'HELP'"
RESULTS           = "Thank you! Here are your results: "
RESULTS_PROCESSED = "%(name)s has collected these results"
INSTRUCTIONS      = "Please record these results in your clinic records and promptly delete them from your phone.  Thank you again %(name)s!"
NOT_REGISTERED    = "Sorry you must be registered with a clinic to check results. " + RegisterHandler.HELP_TEXT
DEMO_FAIL         = "Sorry you must be registered with a clinic or specify in your message to initiate a demo of Results160. To specify a clinic send: DEMO <CLINIC_CODE>"


def build_results_messages(results):
    """
    From a list of lab results, build a list of messages reporting 
    their status
    """
    result_strings = []
    for r in results:
        if r.result is None or len(r.result.strip()) == 0:
            result_strings.append("Sample %s: Not Yet Tested, Lab ID = %s"
                        % (r.requisition_id, r.sample_id))
        elif r.result.upper() in 'IXR':
            result_strings.append("Sample %s: Not Ready, Lab ID = %s, %s" %
            (r.requisition_id, r.sample_id, r.result_detail))
        else:
            result_strings.append("Sample %s: %s, Lab ID = %s" %
            (r.requisition_id, r.get_result_display(), r.sample_id))
    
    result_text, remainder = combine_to_length(result_strings,
                                               length=160-len(RESULTS))
    first_msg = RESULTS + result_text
    responses = [first_msg]
    while remainder:
        next_msg, remainder = combine_to_length(remainder)
        responses.append(next_msg)
    return responses

def combine_to_length(list, delimiter=". ", length=160):
    """
    Combine a list of strings to a maximum of a specified length, using the 
    delimiter to separate them.  Returns the combined strings and the 
    remainder as a tuple.
    """
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
 
