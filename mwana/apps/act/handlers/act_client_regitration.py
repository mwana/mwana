# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import FlowClientRegistration
from mwana.apps.act.models import CHW
from datetime import datetime, timedelta


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s


class ActClientRegistrationHandler(KeywordHandler):
    """
    """

    keyword = "act client|act child|act patient"

    def help(self):
        connection = self.msg.connection
        if CHW.objects.filter(is_active=True, connection=connection):
            chw = CHW.objects.get(is_active=True, connection=connection)
            FlowClientRegistration.objects.filter(community_worker=chw).delete()
            FlowClientRegistration.objects.create(community_worker=chw, start_time=datetime.now(),
                                                  valid_until=datetime.now() + timedelta(hours=5))
            self.respond(
                "Hi %s, to register a client first reply with client's unique ID" % chw.name)
            return

        self.respond("Sorry, you must be registered as a CHW for the ACT Program before you "
                     "can register a client. Reply with HELP ACT if you need to be assisted")

    def handle(self, text):
        self.help()
