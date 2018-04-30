# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime, timedelta

from mwana.apps.anc.models import CommunityWorker
from mwana.apps.anc.models import FlowCommunityWorkerRegistration

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s


class ChwHandler(KeywordHandler):
    """
    """

    keyword = "smag|chw"

    def help(self):
        connection = self.msg.connection
        if CommunityWorker.objects.filter(is_active=True, connection=connection):
            chw = CommunityWorker.objects.get(is_active=True, connection=connection)
            self.respond("Your phone is already registered to %s of %s health facility. Send HELP CHW if you need to be"
                         " assisted or send 555555 to leave %s and then register with the new facility" % (chw.name, chw.facility.name, chw.facility.name))
            return
        FlowCommunityWorkerRegistration.objects.filter(connection=self.msg.connection).delete()
        FlowCommunityWorkerRegistration.objects.create(connection=self.msg.connection, start_time=datetime.now(),
                                                       valid_until=datetime.now() + timedelta(hours=5))
        self.respond("Welcome to the Mother Baby Service Reminder Program. To register as a CHW reply with your name.")

    def handle(self, text):
        self.help()