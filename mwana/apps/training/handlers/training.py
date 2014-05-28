# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.const import get_hub_worker_type
from mwana.const import get_district_worker_type
from mwana.apps.locations.models import Location
from mwana.apps.training.models import TrainingSession
from mwana.apps.labresults.messages import HUB_TRAINING_STOP_NOTIFICATION
from mwana.apps.labresults.messages import HUB_TRAINING_START_NOTIFICATION

from mwana.apps.training.messages import *


class TrainingHandler(KeywordHandler):

    keyword = "training"

    def help(self, action=None):
        if action is None:
            self.respond(START_HELP_TEXT)
        elif action.lower() == "start":
            self.respond(START_HELP_TEXT)
        elif action.lower() == "stop":
            self.respond(STOP_HELP_TEXT)

    def handle(self, text):
        # from pudb import set_trace; set_trace()
        if not self.msg.connections[0].contact:
            self.respond(UNREGISTERED)
            return

        text = text.strip()

        if not text:
            self.respond(START_HELP_TEXT, None)
            return

        tokens = text.split()
        action = tokens[0]

        if action.lower() not in ['start', 'stop']:
            self.help(None)
            return

        if len(tokens) == 1:
            self.help(action=tokens[0])
            return

        if len(tokens) == 2:
            text = tokens[1]

        clinic_code = text[:6]
        try:
            location = Location.objects.get(slug=clinic_code)
        except Location.DoesNotExist:
            self.respond(UNKNOWN_LOCATION % clinic_code)
            return

        contact = self.msg.connections[0].contact

        if action.lower() == "stop":
            trainings_at_site = TrainingSession.objects.filter(
                trainer=contact,
                location=location,
                is_on=True)

            for training in trainings_at_site:
                training.is_on = False
                training.end_date = datetime.utcnow()
                training.save()

            for help_admin in Contact.active.filter(is_help_admin=True):
                OutgoingMessage(help_admin.default_connection,
                                "Training has stopped at %s, %s"
                                ". Notification was sent by %s, %s" %
                                (location.name, location.slug, contact.name,
                                 contact.default_connection.identity)).send()

            hub_workers = Contact.active.filter(
                location__parent=location.parent,
                types=get_hub_worker_type())

            for hub_worker in hub_workers:
                hw_msg = OutgoingMessage(hub_worker.default_connection,
                                         HUB_TRAINING_STOP_NOTIFICATION % {
                                             'hub_worker': hub_worker.name,
                                             'clinic': location.name,
                                             'slug': location.slug})
                hw_msg.send()

            self.respond(TRAINING_STOP % (contact.name, location.name))

        if action.lower() == "start":
            TrainingSession.objects.create(trainer=contact, location=location)

            for help_admin in Contact.active.filter(is_help_admin=True):
                ha_msg = OutgoingMessage(
                    help_admin.default_connection,
                    "Training is starting at %s, %s"
                    ". Notification was sent by %s, %s" %
                    (location.name, location.slug, contact.name,
                     contact.default_connection.identity))
                ha_msg.send()

            hub_workers = Contact.active.filter(
                location__parent=location.parent,
                types=get_hub_worker_type())

            for hub_worker in hub_workers:
                hw_msg = OutgoingMessage(
                    hub_worker.default_connection,
                    HUB_TRAINING_START_NOTIFICATION % {
                        'hub_worker': hub_worker.name,
                        'clinic': location.name,
                        'slug': location.slug})
                hw_msg.send()

            dhos = Contact.active.filter(location=location.parent,
                                         types=get_district_worker_type())

            for contact in dhos:
                hw_msg = OutgoingMessage(
                    contact.default_connection,
                    DHO_TRAINING_START_NOTIFICATION % {
                        'worker': contact.name,
                        'location': location.name,
                        'slug': location.slug})
                hw_msg.send()

            self.respond(TRAINING_START % (contact.name, location.name))
