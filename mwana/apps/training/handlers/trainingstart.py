# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from mwana.apps.training.models import TrainingSession
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact


class TrainingStartHandler(KeywordHandler):

    keyword = "training start|start training|stat training|training stat|traning start|traning stat"

    HELP_TEXT = "To send notification for starting a training , send TRAINING START <CLINIC CODE>"
    UNKNOWN_LOCATION = "Sorry, I don't know about a location with code %(code)s. Please check your code and try again."
    UNGREGISTERED = "Sorry, you must first register with Results160/RemindMI. If you think this message is a mistake, respond with keyword 'HELP'"

    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond(self.UNGREGISTERED)
            return

        text = text.strip()
        if not text:
            self.respond(self.HELP_TEXT)
            return

        clinic_code = text[:6]
        try:
            location = Location.objects.get(slug=clinic_code)
        except Location.DoesNotExist:
            self.respond(self.UNKNOWN_LOCATION, code=clinic_code)
            return

        contact = self.msg.contact
        TrainingSession.objects.create(trainer=contact, location=location)       

        for help_admin in Contact.active.filter(is_help_admin=True):
            ha_msg = OutgoingMessage(help_admin.default_connection,
                                    "Training is starting at %s, %s"
                                    ". Notification was sent by %s, %s" %
                                    (location.name, location.slug, contact.name,
                                    contact.default_connection.identity))
            ha_msg.send()

        self.respond("Thanks %(name)s for your message that training is "
        "starting for %(clinic)s. At end of training please send TRAINING STOP",
                     name=contact.name, clinic=location.name)