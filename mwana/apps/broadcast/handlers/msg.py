# vim: ai ts=4 sts=4 et sw=4
import re
from django.db.models import Q
from mwana.apps.broadcast.handlers.base import BroadcastHandler
from mwana.apps.broadcast.handlers.base import UNREGISTERED
from mwana.const import get_cba_type
from mwana.const import get_clinic_worker_type
from mwana.const import get_district_worker_type
from mwana.util import get_clinic_or_default
from rapidsms.models import Contact

class MessageHandler(BroadcastHandler):
    """
    Extends the capabilities for handlers cba, clinic and all by introducing the
    ditrict level. syntax is MSG <GROUP> <MESSAGE-BODY>
    """

    group_name = "MSG"
    keyword = "msg"

    HELP_TEXT = ("To send a message SEND: MSG <GROUP> <your message>. The groups"
                 " you can send to are: %s")

    PATTERN = re.compile(r"^(all|cba|clinic|dho)(\s+)(.{1,})$")

    workertype_group_mapping = {
    'cba':('cba', 'clinic', 'all'),
    'worker':('cba', 'clinic', 'all', 'dho'),
    'district':('dho', 'clinic', 'all'),
    }
    broadcaster_types = (get_cba_type(), get_clinic_worker_type(), get_district_worker_type())

    def ismatch_sender_group(self, keyword):
        contact_types = self.msg.contact.types.all()        
        for contact_type in contact_types:
            if contact_type.slug in self.workertype_group_mapping.keys() and \
            self.workertype_group_mapping[contact_type.slug]:
                if keyword.lower() in self.workertype_group_mapping[contact_type.slug]:
                    return True
        return False


    def help(self):
        self.respond(self.get_help_text())
        
    def get_help_text(self):
        groups = []
        try:
            for type in self.msg.contact.types.all():                
                for val in self.workertype_group_mapping[type.slug]:
                    groups.append(val)
        except (KeyError):
            pass
        if not groups:
            groups.append('')
        return (self.HELP_TEXT % ", ".join(val.upper() for val in groups))

    def mulformed_message(self):
        self.respond("Sorry, I din't understand that. %s" % self.get_help_text())

    def handle(self, text):
        if self.msg.contact is None or \
            self.msg.contact.location is None:
                self.respond(UNREGISTERED)
                return
        if set(self.msg.contact.types.all()).isdisjoint(set(self.broadcaster_types)):
            self.respond("You are not allowed to send broadcast messages. If "
                         "you think this message is a mistake please reply with"
                         " keyword HELP")
            return

        location = get_clinic_or_default(self.msg.contact)

        group = self.PATTERN.search(text.strip())
        if not group:
            self.mulformed_message()
            return True

        tokens = group.groups()

        msg_part = text[len(tokens[0]):].strip()
        group_name = tokens[0].upper()
        self.group_name = group_name
        if not self.ismatch_sender_group(group_name):
            self.respond("'%s' is not a valid message group for you. %s" % \
                         (group_name, self.get_help_text()))
            return

        contacts = None
        if group_name == "CLINIC":
            contacts = Contact.active.location(location)\
                .exclude(id=self.msg.contact.id)\
                .filter(types=get_clinic_worker_type())
        elif group_name == "CBA":
            contacts = Contact.active.location(location)\
                .exclude(id=self.msg.contact.id)\
                .filter(types=get_cba_type())
        elif group_name == "DHO":
            contacts = Contact.active.filter(Q(location=location) | \
                                             Q(location__location=location) | \
                                             Q(location__parent=location))\
                                            .exclude(id=self.msg.contact.id)\
                                            .filter(types = get_district_worker_type)
        elif group_name == "ALL":
            contacts = Contact.active.location(location)\
                .exclude(id=self.msg.contact.id)
        if contacts:
            return self.broadcast(msg_part, contacts)
        else:
            print 'ooops!'
            self.help()
        


