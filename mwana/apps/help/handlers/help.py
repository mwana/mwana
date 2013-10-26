# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.help.models import HelpRequest
from mwana.util import get_clinic_or_default
from mwana.util import get_contact_type_slug
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.router import send
from rapidsms.models import Contact
_ = lambda s: s

RESPONSE = _("Sorry you're having trouble%(person)s. Your help request has been forwarded to a support team member and they will call you soon.")
ANONYMOUS_FORWARD = "Someone has requested help. Please call them at %(phone)s."
CONTACT_FORWARD = "%(name)s has requested help. Please call them at %(phone)s."
CON_LOC_FORWARD = "%(name)s at %(location)s has requested help. Please call them at %(phone)s."
ADDITIONAL_INFO = "Their message was: %(message)s"


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
                params["location"] = get_clinic_or_default(self.msg.contact)
                resp_template = CON_LOC_FORWARD
            else:
                resp_template = CONTACT_FORWARD

        if text:
            resp_template = resp_template + " " + ADDITIONAL_INFO
            params["message"] = text

        person_arg = " " + self.msg.connection.contact.name if self.msg.connection.contact else ""
        self.respond(RESPONSE % {'person': person_arg})

        connections = []
        help_notice = resp_template % params
        for help_admin in Contact.active.filter(is_help_admin=True):
            connections.append(help_admin.default_connection)

        send(help_notice, connections)
