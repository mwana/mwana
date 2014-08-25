# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.filteredlogs.messagefilter import MessageFilter
from mwana.apps.reports.views import get_admin_email_address
from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from mwana.apps.email.sender import EmailSender
import logging


logger = logging.getLogger(__name__)


class MsgThreadHandler(KeywordHandler):
    """
    Allows help admins to retrieve last few messages for a user
    """

    keyword = "THREAD|CONVERSATION"

    HELP_TEXT = "To receive a message thread for a user, send THREAD <PHONE_NUMBER_PATTERN>"
    UNGREGISTERED = "Sorry, you must be registered as HELP ADMIN to retrieve \
message threads. If you think this message is a mistake, respond with keyword 'HELP'"

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

        phone_number = text.strip()
        limit = 10
        parts = phone_number.split()
        if len(parts) == 2:
            phone_number = parts[0]
            if parts[1].isdigit():
                limit = parts[1]

        contacts = Contact.active.filter(
            connection__identity__contains=phone_number)

        if not contacts:
            self.respond("There are no active SMS users with phone number "
                         "matching %s" % phone_number)
            return True

        msgs = Message.objects.filter(contact__in=contacts).order_by('-date')[:limit]

        main_body = "\n".join("%s %s %s (%s)" % (msg.connection.identity,
                                                 {"I": "<<", "O": ">>"}.get(
                                                     msg.direction, "-"),
                                                 MessageFilter.get_filtered_message(
                                                     msg.text),
                                                 msg.date.strftime("%d/%m/%Y %H:%M")
        ) for msg in msgs)

        self.respond(main_body[:160])

        # TODO: make following execute faster
        email_sender = EmailSender()
        try:
            email_sender.send([get_admin_email_address()], "Messages", main_body)
        except Exception, e:
            logger.error("Error when sending mail: %s" % e.message)
        