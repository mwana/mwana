# vim: ai ts=4 sts=4 et sw=4
import datetime
import logging

from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.patienttracing import models as patienttracing
from datetime import datetime,timedelta
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.patienttracing.models import SentConfirmationMessage

logger = logging.getLogger('mwana.apps.patienttracing.tasks')
_ = lambda s: s

def send_confirmation_reminder(router):
    logger.info("Retrieving PatientTraces for confirmation reminder messages")
    confirmation_reminder_txt = _("Hi %(cba)s! If you know that %(patient)s has been to the clinic, please send: CONFIRM %(name)s")
    DAYS_AFTER_TOLD = 3
    confirm_window_date = (datetime.now() - timedelta(days=DAYS_AFTER_TOLD))
    traces = PatientTrace.objects.filter(status=patienttracing.get_status_told())\
                                    .filter(reminded_date__lte=confirm_window_date)
                                    
    
    for trace in traces:
        logger.info("Found %s traces... Sending confirmation reminders." % str(len(traces)))
        trace.status = patienttracing.get_status_await_confirm()
        trace.save()
        if(trace.messenger is None): 
            logger.info ("Trace (%s) does not have a usable Connection!" % (str(PatientTrace)))
            continue #Can't send confirmation message if we have no one to send it to.
        connection = trace.messenger.default_connection
        message_txt = confirmation_reminder_txt % {'cba':trace.messenger.name, 'patient':trace.name, 'name':trace.name}
        msg = OutgoingMessage(connection, message_txt)
        msg.send()
        scm = SentConfirmationMessage.objects.create(patient_name=trace.name, \
                                                     initiator_contact=trace.initiator_contact,\
                                                     cba_contact=trace.messenger,\
                                                     message = message_txt,\
                                                     sent_date = datetime.now())
        scm.save()
        