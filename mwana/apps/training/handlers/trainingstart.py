# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.labresults.messages import DHO_TRAINING_START_NOTIFICATION
from mwana.apps.labresults.messages import HUB_TRAINING_START_NOTIFICATION
from mwana.apps.locations.models import Location
from mwana.apps.training.models import TrainingSession
from mwana.const import get_district_worker_type
from mwana.const import get_hub_worker_type
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
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


        hub_workers = Contact.active.filter(location__parent=location.parent,
                                            types=get_hub_worker_type())


        for hub_worker in hub_workers:
            hw_msg = OutgoingMessage(hub_worker.default_connection,
                                     HUB_TRAINING_START_NOTIFICATION % {
                                     'hub_worker':hub_worker.name,
                                     'clinic':location.name,
                                     'slug':location.slug})
            hw_msg.send()

        dhos = Contact.active.filter(location=location.parent,
                                     types=get_district_worker_type())


        for contact in dhos:
            hw_msg = OutgoingMessage(contact.default_connection,
                                     DHO_TRAINING_START_NOTIFICATION % {
                                     'contact':contact.name,
                                     'location':location.name,
                                     'slug':location.slug})
            hw_msg.send()



        self.respond("When the trainees finish the course tell them to state "
                     "that they have been trained. Let each one send TRAINED <TRAINER GROUP> <USER TYPE>, E.g Trained zpct cba"
                     )

        self.respond("Thanks %(name)s for your message that training is "
                     "starting for %(clinic)s. At end of training please send TRAINING STOP",
                     name=contact.name, clinic=location.name)