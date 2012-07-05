# vim: ai ts=4 sts=4 et sw=4
from django.db.models import Q
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location


class ContactsHandler(KeywordHandler):
    """
    A simple app, that allows help admins to get the code for a facility
    """

    keyword = "code|facility code"

    HELP_TEXT = "To get the code for a clinic, send <CODE> <CLINIC NAME>"
    UNGREGISTERED = "Sorry, you must be registered as HELP ADMIN to request for \
facility codes. If you think this message is a mistake, respond with keyword 'HELP'"

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

        location_text = text.split()[0][:20]
        
        locations = Location.objects.exclude(type__slug='zone')\
                                    .filter(Q(name__icontains=location_text) |
                                            Q(slug__contains=location_text))[:5]
        
        if locations:
            location_list = "\n**".join(location.slug + "-"
                                        + location.name + "."
                                        for location in locations)
            self.respond(location_list)
        else:
            self.respond("There are no locations matching %s" % text)