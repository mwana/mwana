from mwana.apps.broadcast.handlers.base import BroadcastHandler, UNREGISTERED
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default
from mwana.const import get_district_worker_type
import re

class DistrictHandler(BroadcastHandler):
    
    group_name = "MSG"
    keyword = "msg"
    
    MALFORMED_MESSAGE = "Sorry, we didn't recognise any keywords. Available keywords are: ALL or <CLINIC_NUMBER>. Send: MSG EXAMPLE for an example"
    EXAMPLE_MESSAGE_ONE = "To send to all clinics in your district use: MSG ALL (your message). ** For example: MSG ALL remember to fill out the DBS logbook!"
    EXAMPLE_MESSAGE_TWO = "To send to other DHOs in your district, use: MSG DHO (your message). ** For example: MSG DHO I will be going to all clinics in Mansa this week"
    PATTERN = re.compile(r"^(\w+)(\s+)(.{1,})$")
    def handle(self, text):
        '''
        Sends to all other contacts in the same district
        '''
        if self.msg.contact is None or \
           self.msg.contact.location is None:
            self.respond(UNREGISTERED)
            return
        location = get_clinic_or_default(self.msg.contact)        
        
        
        tokens = text.strip().lower().split(' ')
        if tokens[0] == 'example':
            self.respond(self.EXAMPLE_MESSAGE_ONE)
            self.respond(self.EXAMPLE_MESSAGE_TWO)
            return True
        
        group = self.PATTERN.search(text.strip())
        if not group:
            self.respond(self.MALFORMED_MESSAGE)
            return True
        
        tokens = group.groups()
        if tokens[0].lower() == 'dho':
            contacts = Contact.active.location(location)\
                            .exclude(id=self.msg.contact.id)\
                            .filter(types=get_district_worker_type())
            return self.broadcast(text, contacts)
        elif tokens[0].lower() == 'all':
            contacts = Contact.objects.filter(location__parent__slug__startswith=location.slug)
            return self.broadcast(text, contacts)
            
            
            
            