# vim: ai ts=4 sts=4 et sw=4
import re
from mwana import const
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location, LocationType
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default

_ = lambda s: s


class JoinHandler(KeywordHandler):
    """
    """
    include_type = False
    keyword = "Change clinic|change location|change my clinic|change my location|ChangeClinic|changeLocation|changeMyClinic|changeMyLocation"
    PIN_LENGTH = 4
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 2

    PATTERN = re.compile(r"^(\w+)(\s+)(.{1,})(\s+)(\d+)$")
    HELP_TEXT = "To change your registration status from one clinic to another send <CHANGE CLINIC> <NEW CLINIC CODE> E.g. Change clinic 111111"

    UNGREGISTERED = "You are not currently registered with any location. Reply with HELP if you need to be assisted"

    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        slug = text.strip()

        if not self.msg.contact:
            self.respond(self.UNGREGISTERED)
            return True

        if not self.msg.contact.types.filter(id=const.get_clinic_worker_type().id):
            self.respond("You are not registered as a clinic worker. Please respond with HELP to be assisted.")
            return True

        if len(slug.split()) != 1:
            self.respond(self.HELP_TEXT)
            return True

        try:
            new_location = Location.objects.get(slug__iexact=slug,
                                            type__slug__in=const.CLINIC_SLUGS)

            old_contact = self.msg.contact
            old_clinic = old_contact.location
            if new_location == old_clinic:
                self.respond("You already belong to %(name)s which has clinic code %(slug)s", name=old_clinic.name, slug=slug)
                return True

            new_contact = Contact(location=new_location)
            new_contact.name = old_contact.name
            new_contact.pin = old_contact.pin
            new_contact.save()
            for worker_type in old_contact.types.all():
                new_contact.types.add(worker_type)

            self.msg.connection.contact = new_contact
            self.msg.connection.save()
            old_contact.is_active = False
            old_contact.save()

            self.respond(_("Thank you %(name)s! You have successfully "
                           "changed your location from %(old_clinic)s to %(new_clinic)s."), name=new_contact.name,
                         old_clinic=old_clinic.name, new_clinic=new_contact.location.name)

        except Location.DoesNotExist:
            self.respond(_("Sorry, I don't know about a location with code %(code)s. Please check your code and try again."),
                         code=slug)
