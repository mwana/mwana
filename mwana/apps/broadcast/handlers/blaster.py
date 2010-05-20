from mwana.apps.broadcast.handlers.base import BroadcastHandler, BLASTMESSAGE
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default


class BlastHandler(BroadcastHandler):
    
    group_name = "Mwana Users"
    keyword = "BLAST|blast|blaster|blastar|blasta|blust|bluster|blusta|blustar"
    
    def handle(self, text):
        contacts = Contact.active.exclude(id=self.msg.contact.id)
        return self.broadcast(text, contacts)