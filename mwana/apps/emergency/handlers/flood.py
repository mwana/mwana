# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.emergency.models import FloodReport
from mwana.util import get_clinic_or_default
from mwana.util import get_contact_type_slug
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.router import send
from rapidsms.models import Contact
_ = lambda s: s

RESPONSE = _("Thank you %(person)s. Your report has been logged with the response team.")
ANONYMOUS_FORWARD = "Someone has reported flood data. Please check the report."
CONTACT_FORWARD = "%(name)s on %(phone)s has reported flood data. Please check and classify it."
CON_LOC_FORWARD = "%(name)s at %(location)s has reported flood data. Please check the report."
ADDITIONAL_INFO = "Their message was: %(message)s"
HELP_TEXT = "Please send your information following the FLOOD keyword."


class FloodHandler(KeywordHandler):
    """
    A simple app, that optionally lets you forward requests to help admins
    """

    keyword = "flood|flad|fl00d|food|f00d"

    def help(self):
        # Because we want to process this with just an empty keyword, rather
        # than respond with a help message, just call the handle method from
        # here.
        self.handle("")

    def handle(self, text):
        # create the "ticket" in the db
        FloodReport.objects.create(reported_by=self.msg.connections[0],
                                   additional_text=text[:160])

        params = {"phone": self.msg.connections[0].identity}
        resp_template = ANONYMOUS_FORWARD
        if self.msg.connections[0].contact:
            params["name"] = "%s (%s)" % (
                self.msg.connections[0].contact.name,
                get_contact_type_slug(self.msg.connections[0].contact))
            if self.msg.connections[0].contact.location:
                params["location"] = get_clinic_or_default(self.msg.connections[0].contact)
                resp_template = CON_LOC_FORWARD
            else:
                resp_template = CONTACT_FORWARD

        if text:
            resp_template = resp_template + " " + ADDITIONAL_INFO
            params["message"] = text

        person_arg = " " + self.msg.connections[0].contact.name if self.msg.connections[0].contact else ""
        self.respond(RESPONSE % {'person': person_arg})

        connections = []
        flood_notice = resp_template % params
        for help_admin in Contact.active.filter(is_help_admin=True):
            connections.append(help_admin.default_connection)

        send(flood_notice, connections)
