# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import FlowVisitConfirmation
from mwana.apps.act.util import clear_flows
from mwana.apps.act.models import CHW
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from datetime import datetime, timedelta

_ = lambda s: s


class ActVisitConfirmationHandler(KeywordHandler):
    """
    """

    keyword = "act done|act d0ne"

    def help(self):
        connection = self.msg.connection
        if CHW.objects.filter(is_active=True, connection=connection):
            chw = CHW.objects.get(is_active=True, connection=connection)
            clear_flows(chw)
            FlowVisitConfirmation.objects.create(community_worker=chw, start_time=datetime.now(),
                                                  valid_until=datetime.now() + timedelta(hours=5))
            self.respond(
                "Hi %s, to confirm a client's visit first reply with appointment ID" % chw.name)
            return

        self.respond("Sorry, you must be registered as a CHW for the ACT Program before you "
                     "can confirm a client's visit. Reply with HELP VISIT if you need to be assisted")

    def handle(self, text):
        self.help()
