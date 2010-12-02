# vim: ai ts=4 sts=4 et sw=4
import mwana.const as const
from django.db.models import Q
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location
from rapidsms.models import Contact


class ContactsHandler(KeywordHandler):
    """
    A simple app, that allows help admins to get contacts for a facility
    """

    keyword = "contact|contacts|contuct|contucts|contant|contants"

    HELP_TEXT = "To get active contacts for a clinic, send <CONTACTS> <CLINIC CODE> [<COUNT = {5}>]"
    UNGREGISTERED = "Sorry, you must be registered as HELP ADMIN to request for \
facility contacts. If you think this message is a mistake, respond with keyword 'HELP'"

    def help(self):
        """ Default help handler """
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        # make sure they are registered with the system
        if not (self.msg.contact and self.msg.contact.is_help_admin):
            self.respond(self.UNGREGISTERED)
            return

        text = text.strip()
        if not text:
            self.help()
            return

        location_slug = text.split()[0][0:6] #get only PPDDFF from 1st token
        try:
            txt_count = text.split()[1]
            ic = InputCleaner()
            count = ic.words_to_digits(txt_count)
        except (IndexError, ValueError, AttributeError):
            count = 5
            
        if count == 0:
            count = 5

        try:
            location = Location.objects.get(slug__iexact=location_slug)
        except Location.DoesNotExist:
            self.respond("Sorry, I don't know about a location with code "
                         "%(code)s. Please check your code and try again.",
                         code=location_slug)
            return

        active_contacts = Contact.active.filter(Q(location=location) |
                                                Q(location__parent=location),
                                                Q(types=
                                                const.get_clinic_worker_type()))\
                                                .order_by('pk')
        if active_contacts:
            contact_list = " ****".join(contact.name + ";"
                                        + contact.default_connection.identity + "."
                                        for contact in active_contacts[0:count])
            self.respond("Contacts at %s: %s" %
                         (location.name, contact_list))
        else:
            self.respond("There are no active contacts at %s" % location.name)