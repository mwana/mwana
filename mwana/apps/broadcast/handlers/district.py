from mwana.apps.broadcast.handlers.base import BroadcastHandler, UNREGISTERED
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default
from mwana.const import get_district_worker_type

class DistrictHandler(BroadcastHandler):
    
    group_name = "DISTRICT"
    keyword = "DISTRICT|DHSTRHT|DISTRHT|DHSTRICT|DESTRECT|DISTREECT|district"
    
    
    def handle(self, text):
        '''
        Sends to all other contacts in the same district
        '''
        if self.msg.contact is None or \
           self.msg.contact.location is None:
            self.respond(UNREGISTERED)
            return
        
        location = get_clinic_or_default(self.msg.contact)
        
        contacts = Contact.active.location(location)\
                        .exclude(id=self.msg.contact.id)\
                        .filter(types=get_district_worker_type())
        return self.broadcast(text, contacts)