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

class ToldHandler(KeywordHandler):
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
    
    keyword = "told|toll|teld"
    
    help_txt = "Sorry, the system could not understand your message. To trace a patient please send: TRACE <PATIENT_NAME>"
    unrecognized_txt = "Sorry, the system does not recognise your number.  To join the system please send: JOIN"
    response_told_thanks_txt = "Thank you %s! After %s has visited the clinic, please send us a confirmation message by sending: CONFIRM %s." \
                               "You will receive a reminder to confirm in a few days"
                               
#    patient_not_found_txt = "Sorry %s, we don't have a patient being traced by that name. Did you check the spelling of the patient's name?"
#    trace_expired_txt = "Sorry %s, the trace for %s has expired.  Please check the spelling of the patient's name if you are sure a trace has been initiated"\
#                        "in the last %s days"
                        
#    initiator_status_update_txt = "Hi %s, CBA %s has just told %s to come to the clinic."
    
    
    def handle(self,text):
        #check message is valid
        #check for:
        # CONTACT is valid
        # FORMAT is valid
        # 
        #pass it off to trace() for processing.
        words = self.sanitize_and_validate(text)
        if words:
            return self.told(words)
        else:
            return
        
    def sanitize_and_validate(self, text):
        #check if contact is valid
        if self.msg.connection.contact is None \
               or not self.msg.connection.contact.is_active:
            self.unrecognized_sender()
            return None
        
        return text
    
    
    def create_new_patient_trace(self, pat_name):
        p = PatientTrace.objects.create(clinic = self.msg.connection.contact.location.parent)
        p.initiator_contact = self.msg.connection.contact
        p.type="unrecognized_patient"
        p.name = pat_name
        p.status = patienttracing.get_status_new()
        p.start_date = datetime.now() 
        p.save()
        
    def told(self, pat_name):
        '''
        Respond to TOLD message, update PatientTrace db entry status to 'told'
        '''

        #Check to see if there are any patients being traced by the given name        
        patients = PatientTrace.objects.filter(name__iexact=pat_name) \
                                        .filter(status=patienttracing.get_status_new()) \
                                        .filter(clinic = self.msg.connection.contact.location.parent)
        
        if len(patients) == 0:
#            self.respond("patient "+pat_name+" not found! Making a new one!")
            #if no matching trace is found
            self.create_new_patient_trace(pat_name)
            self.told(pat_name) #redo the loop
            return True
            
        #If there are more than one patients in the resulting list, pick the first one.  We have no way
        #of knowing which one is the correct patient in this case.
        patient = patients[0]
        
        #update patienttrace entry data
        patient.reminded_date = datetime.now()
        patient.status = patienttracing.get_status_told()
        patient.messenger = self.msg.connection.contact
        
        patient.save()
        
        self.respond_told_thankyou(pat_name)
    
    
#    def respond_trace_expired(self,pat_name):
#        self.respond(self.trace_expired_txt % (self.msg.connection.contact.name, pat_name, self.TRACE_WINDOW))
         
#    def respond_patient_not_found(self,pat_name):
#        self.respond(self.patient_not_found_txt % (self.msg.connection.contact.name))
         
    def respond_told_thankyou(self, pat_name):
        '''
        Responds with a thank you message for telling the patient to come into the clinic,
        Informs the user about confirming the visit
        '''
        self.respond(self.response_told_thanks_txt % (self.msg.connection.contact.name, pat_name, pat_name))
        
 
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
    

    
#    def update_initiator_on_status(self,pat_name, initiator_contact):
#        self.respond(self.initiator_status_update_txt % (initiator_contact.name, self.msg.connection.contact.name, pat_name))
        



    