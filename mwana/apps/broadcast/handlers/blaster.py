# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.broadcast.handlers.base import BroadcastHandler, UNREGISTERED
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default


class BlastHandler(BroadcastHandler):
    
    group_name = "Mwana Users"
    keyword = "blast|blust|blaster|bluster|blastar|blustar|blasta|blusta"
    
    def handle(self, text):
        if self.msg.contact is not None and self.msg.contact.is_help_admin and self.msg.contact.is_active:
            contacts = Contact.active.exclude(id=self.msg.contact.id)
            return self.broadcast(text, contacts)
              