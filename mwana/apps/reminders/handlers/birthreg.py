#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from mwana.apps.labresults.util import is_eligible_for_results
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.reminders.models import PatientEvent

class BirthregHandler(KeywordHandler):
    """
    """

    keyword = "birthreg|newborn|newbirth|bethreg|newbon|newbone|newborne"

#    PATTERN = re.compile(r"^(\w+)(\s+)(.{4,})(\s+)(\d+)$")
    
    PIN_LENGTH = 4     
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 1

    HELP_TEXT = "To recieve new births, send birthreg <PIN>"
    NOT_ELIGIBLE = "I am sorry, you do not have permission to view new births."
    BAD_PIN = "Invalid PIN number. Please send: birthreg <PIN> "
        
    def help(self):
        self.respond(self.HELP_TEXT)    

    def get_locations_with_births(self):
        locs=[]
#        births = PatientEvent.objects.filter(event='birth')
        births = PatientEvent.objects.filter(notification_status='new')
        for birth in births:
            try:
                location= birth.cba_conn.contact.location.parent
                if location not in locs:
                    locs.append(location)
            except AttributeError:
                pass
        return locs


    def handle(self, text):
        
        if not is_eligible_for_results(self.msg.connection):
            self.respond(self.NOT_ELIGIBLE)
            return
        if not text or not text.strip():
            return
        
        pin = text.split()[0]
        
        text = text.strip()
        
        text2 = self.msg.contact.pin
        if text2 == text:
            
            staff_name = self.msg.contact.name
            staff_location = self.msg.contact.location
            pe = PatientEvent.objects.filter(notification_status='new').\
                filter(cba_conn__contact__location__parent=staff_location)

            str = ''
            str = ", ".join(i.patient.name + ":"+ i.date.strftime("%d/%m/%Y") for i in pe.all() )
            self.respond("Hello %s! The births from %s are: ***%s" % (staff_name, staff_location, str))
            return
        
        msg = self.BAD_PIN
        
        self.respond(msg)
                                          
