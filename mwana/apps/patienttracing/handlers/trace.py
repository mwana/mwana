# vim: ai ts=4 sts=4 et sw=4
import re
import logging
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.patienttracing.models import PatientTrace
from datetime import datetime
from rapidsms.models import Contact
from rapidsms.router import send
from mwana.util import get_clinic_or_default
from mwana.apps.broadcast.models import BroadcastMessage
from mwana.const import get_cba_type
from mwana.apps.patienttracing import models as patienttracing
from mwana.apps.labresults.util import is_already_valid_connection_type as is_valid_connection
from mwana import const

_ = lambda s: s
logger = logging.getLogger(__name__)


class TraceHandler(KeywordHandler):
    '''User sends: TRACE MARY <REASON> (Reason is optional)

    Where Mary is the patient's name.  Message goes out to all CBAs asking them
    to find and talk to Mary.  It also asks them to reply with the message,

    TOLD MARY

    once they have spoken to the patient and asked them to go to the clinic.

    After a set period of time a follow up message will go out of from the
    system to the CBA that replied asking them to follow up with Mary and
    confirm that she did indeed go to the clinic.  This is done by having the
    CBA send the following message to the system: CONFIRM MARY

    '''

    keyword = "trace|trase|trac|tress|traice|tras|find|fhnd"

    help_txt = "Sorry, the system could not understand your message. To "\
               "trace a patient please send: TRACE <PATIENT_NAME|ID>"
    unrecognized_txt = "Sorry, the system does not recognise your number."\
                       " To join the system please send: JOIN"
    response_to_trace_txt = "Thank you %s. Mobile Agents have been asked"\
                            " to find %s."
    cba_initiate_trace_msg = "Hello, please meet %(cworker)s at the clinic for "\
                             "information on tracing %(name)s."

    cba_not_allowed_txt = "Sorry %s, CBAs are not allowed to start Traces."\
                          "  Please ask a clinic worker to start a trace."

    def handle(self, text):
        if not self.contact_valid():
            return
        mytext = text.lower().replace("&", ",").replace(
            " and", ",").replace(".", ",")
        for name in mytext.split(","):
            if len(name) > 50:
                self.respond("%s is too long for a name." % name)
            elif name:
                self.man_trace(name.title())
        return True

    def contact_valid(self):
        connection = self.msg.connection
       # only clinic workers should be able to trace
        if not is_valid_connection(connection, const.get_clinic_worker_type()):
            if is_valid_connection(connection, const.get_cba_type()):
                self.respond(self.cba_not_allowed_txt % (
                    self.msg.connection.contact.name))
            else:
                self.unrecognized_sender()
            return False
        else:
            return True

    def man_trace(self, name):
        '''
        Initiate a "manual" trace
        '''
    #    create entry in the model (PatientTrace)
    #    send out response message(s)
        p = PatientTrace.objects.create(
            clinic=self.msg.connection.contact.location)
        p.initiator_contact = self.msg.connection.contact
        p.type = patienttracing.get_type_manual()
        p.initiator = patienttracing.get_initiator_clinic_worker()
        p.name = name
        p.status = patienttracing.get_status_new()
        p.start_date = datetime.now()
        p.save()

        self.respond_trace_initiated(name)
        # send to patient if they have a number otherwise to CHWs
        # create the patient if none existent, plan move to rapidsms-healthcare
        if "_" in name:
            firstname, lastname = name.split("_")
        else:
            firstname = lastname = ''
        patient, created = Contact.objects.get_or_create(
            name=name,
            location=self.msg.connection.contact.location,
            first_name=firstname,
            last_name=lastname)

        if created:
            patient_t = const.get_patient_type()
            if not patient.types.filter(pk=patient_t.pk).count():
                patient.types.add(patient_t)

        if patient.default_connection is not None:
            params = {'first': firstname, 'last': lastname,
                      'clinic': p.clinic.name}
            msg = "Please visit the %(clinic)s clinic for your appointment."
            send(msg % params, [patient.default_connection])
        else:
            self.send_trace_to_cbas(name)

    def respond_trace_initiated(self, patient_name):
        '''
        Respond with an outgoing message back to the sender that a trace has
        been initiated.
        '''

        self.respond(self.response_to_trace_txt % (
            self.msg.connection.contact.name, patient_name))
        pass

    def send_trace_to_cbas(self, patient_name):
        '''
        Sends CBAs the initiate trace message
        '''
        location = get_clinic_or_default(self.msg.connection.contact)

        cbas = Contact.active.location(location).exclude(
            id=self.msg.connection.contact.id).filter(types=get_cba_type())

        for contact in cbas:
            if contact.default_connection is None:
                pass
            else:
                msg = self.cba_initiate_trace_msg % dict(
                    name=patient_name,
                    cworker=self.msg.connection.contact.name)
                send(msg, [contact.default_connection])
        # self.broadcast(self.cba_initiate_trace_msg, cbas, "CHWs", patient_name)

    def help(self):
        '''
        Respond with a help message in the event of a malformed msg or if no
        name was supplied
        '''
        self.respond(self.help_txt)

    def unrecognized_sender(self):
        '''
        Respond with a message indicating that the sender is not
        recognized/authorized to initiate traces
        '''
        self.respond(self.unrecognized_txt)

    def broadcast(self, text, contacts, patient_name):
        group_name = "CHWs"
        for contact in contacts:
            if contact.default_connection is None:
                logger.info(
                    "Can't send to %s as they have no connections" % contact)
            else:
                send(text % dict(name=patient_name),
                     [contact.default_connection])

        logger_msg = getattr(self.msg, "logger_msg", None)
        if not logger_msg:
            logger.error(
                "No logger message found for %s. Is the message log app"
                " running?" % self.msg)
        bmsg = BroadcastMessage.objects.create(logger_message=logger_msg,
                                               contact=self.msg.connection.contact,
                                               text=text,
                                               group=group_name)
        bmsg.recipients = contacts
        bmsg.save()
        return True


# ====================================================================
#    DELETE ME!
#
#    initiator = models.ForeignKey(Contact, related_name='patients_traced',
#                                     limit_choices_to={'types__slug': 'clinic_worker'},
#                                     null=True, blank=True)
#    type = models.CharField(max_length=15)
#    name = models.CharField(max_length=50) # name of patient to trace
#    patient_event = models.ForeignKey(PatientEvent, related_name='patient_traces',
#                                      null=True, blank=True)
#    messenger = models.ForeignKey(Contact,  related_name='patients_reminded',
#                            limit_choices_to={'types__slug': 'cba'}, null=True,
#                            blank=True)# cba who informs patient
#
#    confirmed_by = models.ForeignKey(Contact, related_name='patient_traces_confirmed',
#                            limit_choices_to={'types__slug': 'cba'}, null=True,
#                            blank=True)# cba who confirms that patient visited clinic
#
#    status = models.CharField(choices=STATUS_CHOICES, max_length=15) # status of tracing activity
#
#    start_date = models.DateTimeField() # date when tracing starts
#    reminded_on = models.DateTimeField(null=True, blank=True) # date when cba tells mother
#    confirmed_date = models.DateTimeField(null=True, blank=True)# date of confirmation that patient visited clinic
#
# =======================================================================
