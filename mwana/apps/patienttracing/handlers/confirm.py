# vim: ai ts=4 sts=4 et sw=4
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
from mwana.apps.labresults.util import is_already_valid_connection_type as is_valid_connection
from mwana import const

class ConfirmHandler(KeywordHandler):
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
    
    keyword = "confirm|conferm|confhrm|cnfrm|CONFIRM|Confirm|comfirm|comferm|comfhrm|cmfrm|CONFIRM|Comfirm"
#    PATTERN = re.compile(r"^(\w+)(\s+)(.{1,})(\s+)(\d+)$")  #TODO: FIX ME
    
    help_txt = "Sorry, the system could not understand your message. To confirm a patient has been to the clinic please send: CONFIRM <PATIENT_NAME>"
    unrecognized_txt = "Sorry, the system does not recognise your number.  To join the system please send: JOIN"
    response_confirmed_thanks_txt = "Thank you %s! You have confirmed that %s has been to the clinic!"
                               
    patient_not_found_txt = "Sorry %s, we don't have a patient being traced by that name. Did you check the spelling of the patient's name?"
    
    clinic_worker_not_allowed = "Sorry %s, only CBAs can trace patients.  Please ask the CBA to find the patient."
    initiator_status_update_txt = "Hi %s, CBA %s has CONFIRMED that %s has been to the clinic."


#    trace_expired_txt = "Sorry %s, the trace for %s has expired.  Please check the spelling of the patient's name if you are sure a trace has been initiated"\
#                        "in the last %s days and try again"
    
    def handle(self,text):
        #check message is valid
        #check for:
        # CONTACT is valid        
        if not self.contact_valid():
            return
        
        self.confirm(text)
        return True

    def contact_valid(self):
        if not is_valid_connection(self.msg.connection, const.get_cba_type()): #Only clinic workers should be able to trace
            if is_valid_connection(self.msg.connection, const.get_clinic_worker_type()):
                self.respond(self.clinic_worker_not_allowed % (self.msg.connection.contact.name))
            else:
                self.respond(self.unrecognized_txt)
            return False
        else:
            return True
        
        return True
    
    
                
    def create_new_patient_trace(self, pat_name):
        p = PatientTrace.objects.create(clinic = self.msg.connection.contact.location.parent)
        p.initiator_contact = self.msg.connection.contact
        p.initiator = patienttracing.get_initiator_cba()
        p.type = patienttracing.get_type_unrecognized()
        p.name = pat_name
        p.status = patienttracing.get_status_confirmed()
        p.confirmed_date = datetime.now() 
        p.save()
        
    def confirm(self, pat_name):
        '''
        Respond to CONFIRM message, update PatientTrace db entry status to 'CONFIRM'
        '''

        #Check to see if there are any patients being traced by the given name        
        patients = PatientTrace.objects.filter(name__iexact=pat_name)\
                                        .filter(status=patienttracing.get_status_told())\
                                        .filter(clinic=self.msg.connection.contact.location.parent)
        
        #If patient not found (a name mismatch?) then just deal with it by creating a new 'confirmed' trace entry and thanking the user.
        if len(patients) == 0:
            self.create_new_patient_trace(pat_name)
            self.respond_confirmed_thankyou(pat_name)
            return True

            
        #If there are more than one patients in the resulting list, pick the first one.  We have no way
        #of knowing which one is the correct patient in this case.
        patient = patients[0]
        
        if patient.initiator == patienttracing.get_initiator_clinic_worker() and \
                                            patient.initiator_contact is not None:
            self.update_initiator_on_status(pat_name, patient.initiator_contact)
        
        #update patienttrace entry data
        patient.confirmed_date = datetime.now()
        patient.status = patienttracing.get_status_confirmed()
        patient.messenger = self.msg.connection.contact
        
        patient.save()
        self.respond_confirmed_thankyou(pat_name)
    
#    def respond_trace_expired(self,pat_name):
#        self.respond(self.trace_expired_txt)
         
    def respond_patient_not_found(self,pat_name):
        self.respond(self.patient_not_found_txt % (self.msg.connection.contact.name))
         
    def respond_confirmed_thankyou(self, pat_name):
        '''
        Responds with a thank you message for telling the patient to come into the clinic,
        Informs the user about confirming the visit
        '''
        self.respond(self.response_confirmed_thanks_txt % (self.msg.connection.contact.name, pat_name))
        
 
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
        
        
    def update_initiator_on_status(self,pat_name, initiator_contact):
        if initiator_contact.default_connection is not None:
            msg = OutgoingMessage(initiator_contact.default_connection, self.initiator_status_update_txt % (initiator_contact.name, self.msg.connection.contact.name, pat_name))
            msg.send()

    

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
    
    