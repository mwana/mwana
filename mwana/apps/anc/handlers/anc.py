# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.anc.messages import WELCOME_MSG_A, WELCOME_MSG_B
from mwana.apps.locations.models import Location
from mwana.apps.anc.models import EducationalMessage
from mwana.apps.anc.models import Client
from mwana.apps.anc.models import SentMessage

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


_ = lambda s: s

class AncHandler(KeywordHandler):
    """
    """

    keyword = "anc"
    
    HELP_TEXT = _("To subscribe, Send ANC <CLINIC-CODE> <GESTATIONAL-AGE IN WEEKS>, E.g. ANC 504033 8")
    MALFORMED_MSG_TXT = "Sorry, I didn't understand that. " + HELP_TEXT
    
    def help(self):
        self.respond(self.HELP_TEXT)

    def mulformed_msg_help(self):
        self.respond(self.MALFORMED_MSG_TXT)

    def handle(self, text):
        tokens = text.replace('weeks', '').replace('week', '').replace('wks', '').replace('weaks', '').\
            replace('weak', '').replace('wk', '').strip().split()
        if len(tokens) != 2:
            self.mulformed_msg_help()
            return True
        phone_number = self.msg.connection.identity
        # TODO: Add validations like client cannot have two different pregnancies
        # alternatively just update pregnancy to current gestational age
        slug = tokens[0]
        gestational_age_str = tokens[1]
        locations = Location.objects.filter(slug=slug)
        if not locations:
            self.respond(
                _("Sorry, I don't know about a location with code %(code)s. "
                  "Please check your code and try again."),
                code=slug)
            return
        facility = locations[0]
        if not gestational_age_str.isdigit():
            self.mulformed_msg_help()
            return
        gestational_age = int(gestational_age_str)

        if gestational_age < 0 or gestational_age > 40:
            self.respond("Sorry you cannot subscribe when your gestational age is already 40 or above")
            return

        Client.objects.get_or_create(gestation_at_subscription=gestational_age,
                              lmp=Client.find_lmp(gestational_age), facility=facility,
                              connection=self.msg.connection)

        self.respond("You have successfully subscribed from %s clinic and your "
                     "gestational age is %s. Resubmit if this is incorrect" %
                     (facility.name, gestational_age))
        self.respond(WELCOME_MSG_A)
        self.respond(WELCOME_MSG_B)
        return True