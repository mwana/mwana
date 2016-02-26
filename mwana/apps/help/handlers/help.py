# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

from mwana.apps.help.models import HelpRequest
from mwana.apps.locations.models import Location
from mwana.apps.training.models import TrainingSession
from mwana.const import get_cba_type
from mwana.util import get_clinic_or_default
from mwana.util import get_contact_type_slug
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Contact
from django.db.models import Q

_ = lambda s: s

RESPONSE           = _("Sorry you're having trouble%(person)s. Your help request has been forwarded to a support team member and they will call you soon.")
ANONYMOUS_FORWARD  = "Someone has requested help. Please call them at %(phone)s."
CONTACT_FORWARD    = "%(name)s has requested help. Please call them at %(phone)s."
CON_LOC_FORWARD    = "%(name)s at %(location)s has requested help. Please call them at %(phone)s."
ADDITIONAL_INFO    = "Their message was: %(message)s"

class HelpHandler(KeywordHandler):
    """
    A simple help app, that optionally lets you forward requests to help admins
    """

    keyword = "help|helpme|support|heip|hellp|heup"    
    
    def help(self):
        # Because we want to process this with just an empty keyword, rather
        # than respond with a help message, just call the handle method from
        # here.
        self.handle("")
    
    def handle(self, text):
        
        # create the "ticket" in the db
        HelpRequest.objects.create(requested_by=self.msg.connection,
                                   additional_text=text[:160])
        
        params = {"phone": self.msg.connection.identity}
        resp_template = ANONYMOUS_FORWARD
        if self.msg.connection.contact:
            params["name"] = "%s (%s)" % (self.msg.connection.contact.name,
                                          get_contact_type_slug(self.msg.contact))
            if self.msg.connection.contact.location:
                params["location"] = "%s(%s)" % (get_clinic_or_default(self.msg.contact),
                                                 get_clinic_or_default(self.msg.contact).slug)
                resp_template = CON_LOC_FORWARD
            else: 
                resp_template = CONTACT_FORWARD
        
        if text:
            resp_template = resp_template + " " + ADDITIONAL_INFO
            params["message"] = text

        contact = self.msg.connection.contact

        # Don't forward any but the first help requests for a facility where
        # there is training
        today = datetime.today()
        user_location = get_clinic_or_default(contact)
        user_current_trainings = TrainingSession.objects.filter(location=user_location, is_on=True,
                                                                start_date__year=today.year,
                                                                start_date__month=today.month,
                                                                start_date__day=today.day)
        # count of help requests for this user's location today
        user_helps_today = HelpRequest.objects.filter(requested_by__contact__location=user_location,
                                                      requested_on__year=today.year,
                                                      requested_on__month=today.month,
                                                      requested_on__day=today.day).count()
        if contact and (get_cba_type() in contact.types.all()):
            user_helps_today = HelpRequest.objects.filter(Q(requested_by__contact__location=user_location) |
                                                          Q(requested_by__contact__location__parent=user_location),
                                                          Q(requested_on__year=today.year,
                                                          requested_on__month=today.month,
                                                          requested_on__day=today.day)).count()
        
        if not (contact and user_current_trainings and user_helps_today > 1):
            for help_admin in Contact.active.filter(is_help_admin=True):
                # if support admin is set to receive help requests for specific
                # locations, don't forward them requests from other locations
                if contact and contact.location:
                    admin_clinics = Location.objects.filter(groupfacilitymapping__group__helpadmingroup__contact=help_admin)
                    admin_districts = Location.objects.filter(location__in=admin_clinics)
                    admin_provinces = Location.objects.filter(location__in=admin_districts)
                    if admin_clinics:
                        location  = get_clinic_or_default(contact)
                        if not (location in admin_clinics or location in admin_districts or location in admin_provinces):
                            continue

                OutgoingMessage(help_admin.default_connection, resp_template, ** params).send()
        
        person_arg = " " + self.msg.connection.contact.name if self.msg.connection.contact else ""
        self.respond(RESPONSE, person=person_arg)
                                         
        