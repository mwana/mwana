import re
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.patienttracing import models as patienttracing
from datetime import datetime, timedelta
from rapidsms.models import Contact
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.util import get_clinic_or_default
from mwana.apps.broadcast.models import BroadcastMessage
from mwana.const import get_cba_type

class TraceHandler(KeywordHandler):
    '''
    User sends: 
    TRACE MARY <REASON>
    (Reason is optional)
    Where mary is patient's name.  Message goes out to all CBAs asking them to find and talk to Mary.  
    It also asks them to reply with the message, 
    TOLD MARY
    once they have spoken to the patient and asked them to go to the clinic.
    
    After a set period of time a follow up message will go out of from the system to the CBA that replied
    asking them to follow up with Mary and confirm that she did indeed go to the clinic.
    This is done by having the CBA send the following message to the system:
    CONFIRM MARY
    '''
    
    
    TRACE_WINDOW = 5 #days
    
    keyword = "trace|trase|trac"
    PATTERN = re.compile(r"^(\w+)(\s+)(.{1,})(\s+)(\d+)$")  #TODO: FIX ME
    
    help_txt = "Sorry, the system could not understand your message. To trace a patient please send: TRACE <PATIENT_NAME>"
    unrecognized_txt = "Sorry, the system does not recognise your number.  To join the system please send: JOIN"
    response_told_thanks_txt = "Thank you %s! After %s has visited the clinic, please send us a confirmation message by sending: CONFIRM %s." \
                               "You will receive a reminder to confirm in a few days"
                               
    patient_not_found_txt = "Sorry %s, we don't have a patient being traced by that name. Did you check the spelling of the patient's name?"
    trace_expired_txt = "Sorry %s, the trace for %s has expired.  Please check the spelling of the patient's name if you are sure a trace has been initiated"\
                        "in the last %s days"
    
    def handle(self,text):
        #check message is valid
        #check for:
        # CONTACT is valid
        # FORMAT is valid
        # 
        #pass it off to trace() for processing.
        
        
        
        self.man_trace(text)
        return True
        
    
    def told(self, pat_name):
        '''
        Respond to TOLD message, update PatientTrace db entry status to 'told'
        '''

        #Check to see if there are any patients being traced by the given name        
        patients = PatientTrace.objects.filter(name=pat_name)
        if len(patients) == 0:
            self.respond_patient_not_found(pat_name)

        #Check to see if there is a PatientTrace initiated within the last TRACE_WINDOW days            
        patients.filter(start_date__gt=(datetime.now()-timedelta(days=self.TRACE_WINDOW)))
        
        if len(patients) == 0:
            self.respond_trace_expired(pat_name)
            
        #If there are more than one patients in the resulting list, pick the first one.  We have no way
        #of knowing which one is the correct patient in this case.
        patient = patients[0]
        
        #update patienttrace entry data
        patient.reminded_on = datetime.now()
        patient.status = patienttracing.get_status_told()
        patient.messenger = self.msg.connection.contact
        
        patient.save()
        
        
        self.respond_trace_initiated(name)        
        self.send_trace_to_cbas(name)
     
    
    
    def respond_trace_expired(self,pat_name):
        self.respond(self.trace_expired_txt)
         
    def respond_patient_not_found(self,pat_name):
        self.respond(self.patient_not_found_txt)
         
    def respond_told_thankyou(self):
        '''
        Responds with a thank you message for telling the patient to come into the clinic,
        Informs the user about confirming the visit
        '''
        self.respond(self.response_told_thanks_txt)
        
 
    def help(self):
        '''
        Respond with a help message in the event of a malformed msg or if no name was supplied
        '''
        self.respond(self.help_txt)
    
    def unrecognized_sender(self):
        '''
        Respond with a message indicating that the sender is not recognized/authorized to initiate
        traces
        '''
        self.respond(self.unrecognized_txt)
        pass
    
    
    def respond_thanks_and_confirm_reminder(self,pat_name):
        self.respond(self.response_told_thanks_txt)


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
    
    