from mwana.apps.broadcast.handlers.base import BroadcastHandler, UNREGISTERED
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default
from mwana.const import get_cba_type


class CBAHandler(BroadcastHandler):
    
    group_name = "CBA"
    keyword = "CBA|aaa|cab"
    
    def handle(self, text):
        if self.msg.contact is None or \
           self.msg.contact.location is None:
            self.respond(UNREGISTERED)
            return
        
        location = get_clinic_or_default(self.msg.contact)
        contacts = Contact.active.location(location)\
                        .exclude(id=self.msg.contact.id)\
                        .filter(types=get_cba_type())
        return self.broadcast(text, contacts)