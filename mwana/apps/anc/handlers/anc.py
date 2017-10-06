# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime, timedelta

from mwana.apps.anc.models import CommunityWorker, FlowClientRegistration

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s


class AncHandler(KeywordHandler):
    """
    """

    keyword = "anc"

    HELP_TEXT = _("To subscribe, Send ANC <CLINIC-CODE> <GESTATIONAL-AGE IN WEEKS>, E.g. ANC 504033 8")
    MALFORMED_MSG_TXT = "Sorry, I didn't understand that. " + HELP_TEXT

    def help(self):
        connection = self.msg.connection
        if CommunityWorker.objects.filter(is_active=True, connection=connection):
            chw = CommunityWorker.objects.get(is_active=True, connection=connection)
            FlowClientRegistration.objects.filter(community_worker=chw).delete()
            FlowClientRegistration.objects.create(community_worker=chw, start_time=datetime.now(),
                                                  valid_until=datetime.now() + timedelta(hours=5))
            # TODO: configure supported numbers in database
            self.respond(
                "Hi %s, to register a pregnancy first reply with mother's Airtel or MTN phone number" % chw.name)
            return

        self.respond("Sorry, you must be registered as a CHW for the Mother Baby Service Reminder Program before you "
                     "can register a pregnancy. Reply with HELP ANC if you need to be assisted")

    def handle(self, text):
        self.help()
