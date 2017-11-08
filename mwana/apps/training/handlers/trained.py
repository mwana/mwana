# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.training.models import Trained
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class TrainedHandler(KeywordHandler):

    keyword = "trained|trainied|traned|traind"

    HELP_TEXT = "To state that you have been trained, send TRAINED <TRAINER GROUP> <USER TYPE>. E.g Trained ZPCT cba"
    UNGREGISTERED = "Sorry, you must first register with Results160/RemindMI. If you think this message is a mistake, respond with keyword 'HELP'"

    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond(self.UNGREGISTERED)
            return

        phone = self.msg.contact.default_connection.identity
        contact = self.msg.contact
        if Trained.objects.filter(phone=phone, location=contact.location, name=contact.name, date=date.today()):
            trained = Trained.objects.get(phone=phone, location=contact.location, name=contact.name, date=date.today())
        else:
            text = text.strip()

            trained = Trained()
            trained.name = contact.name
            trained.location = contact.location
            trained.type = contact.types.all()[0]
            trained.phone = contact.default_connection.identity
            trained.additional_text = text
            if text:
                trainer_group = text.split()[0]
                if ReportingGroup.objects.filter(name__iexact=trainer_group).count() == 1:
                    trained.trained_by = ReportingGroup.objects.get(name__iexact=trainer_group)
                    
            trained.save()

        self.respond("Thanks %(name)s. You have been trained as %(type)s at %(location)s",
                     name=trained.name, location=trained.location.name, type=trained.type)