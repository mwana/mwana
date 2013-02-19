# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.blacklist.models import BlacklistedPeople
import rapidsms
from rapidsms.models import Contact
from rapidsms.messages import OutgoingMessage
import logging


logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):


    def handle(self, message):
        """
        block blacklisted users
        """
        if BlacklistedPeople.objects.filter(phone__icontains=message.connection.identity[-10:]):
            message.respond("Your number has been blocked from using Mwana. This incident has been reported")

            for contact in Contact.active.filter(is_help_admin=True):
                msg_text = "This blacklisted number is trying to use the system %s" % (message.connection.identity)
                OutgoingMessage(contact.default_connection, msg_text).send()

            return True

      