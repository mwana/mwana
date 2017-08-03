# vim: ai ts=4 sts=4 et sw=4
from rapidsms.log.mixin import LoggerMixin
from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.anc.models import Client, EducationalMessage
from mwana.apps.anc.messages import DEMO_FAIL
from mwana.apps.locations.models import Location


class MockANCUtility(LoggerMixin):
    """
    A mock data utility.  This allows you to script some demo/testing scripts
    """

    def fake_sending_anc_messages(self, clinic):
        for client in Client.objects.filter(is_active=True):
            if not client.is_eligible_for_messages():
                continue
            age = client.get_gestational_age()
            educational_msgs = EducationalMessage.objects.filter(gestational_age=age)
            if not educational_msgs:
                continue
            for ed in educational_msgs:
                OutgoingMessage(client.connection, ed.text).send()

    def handle(self, message):
        if message.text.strip().upper().startswith("ANCDEMO"):
            rest = message.text.strip()[4:].strip()
            clinic = None
            if rest:
                # optionally allow the tester to pass in a clinic code
                try:
                    clinic = Location.objects.get(slug__iexact=rest)
                except Location.DoesNotExist:
                    # maybe they just passed along some extra text
                    pass
            if not clinic and message.connection.contact \
                and message.connection.contact.location:
                    # They were already registered for a particular clinic
                    # so assume they want to use that one.
                    clinic = message.connection.contact.location
            if not clinic:
                message.respond(DEMO_FAIL)
            else:
                self.info("Initiating a demo sequence to clinic: %s" % clinic)
                self.fake_sending_anc_messages(clinic)
            return True
