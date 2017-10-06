# vim: ai ts=4 sts=4 et sw=4


from mwana.apps.anc.messages import WELCOME_MSG_B
from mwana.apps.anc.models import Client

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s


class AncHandler(KeywordHandler):
    """
    """

    keyword = "age"

    HELP_TEXT = _("To record your gestation age, Send AGE <GESTATIONAL-AGE IN WEEKS>, E.g. AGE 8")
   
    def help(self):
       self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not text.strip().isdigit():
            self.help()
        if Client.objects.filter(is_active=True, connection=self.msg.connection, phone_confirmed=False):
            client = Client.objects.get(is_active=True, connection=self.msg.connection, phone_confirmed=False)
            gestational_age = abs(int(text.strip()))
            if gestational_age > 40:
                self.respond("Sorry you cannot subscribe when your gestational age is already 40 or above")
                return True
            client.gestation_at_subscription = gestational_age
            client.age_confirmed = True
            client.save()
            self.respond(WELCOME_MSG_B)
            return True
        elif Client.objects.filter(is_active=True, connection=self.msg.connection, age_confirmed=False):
            client = Client.objects.get(is_active=True, connection=self.msg.connection, age_confirmed=False)
            gestational_age = abs(int(text.strip()))
            if gestational_age > 40:
                self.respond("Sorry you cannot subscribe when your gestational age is already 40 or above")
                return True
            client.gestation_at_subscription = gestational_age
            client.lmp = Client.find_lmp(gestational_age)
            client.age_confirmed = True
            client.save()
            self.respond(WELCOME_MSG_B)
            return True

        self.respond("To register a pregnancy ask your community health worker to do it for you")