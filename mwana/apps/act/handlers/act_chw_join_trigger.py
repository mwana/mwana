# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import FlowCHWRegistration
from mwana.apps.act.models import CHW
from datetime import datetime, timedelta


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s


class ActChwHandler(KeywordHandler):
    """
    """

    keyword = "actchw|act chw"

    def help(self):
        connection = self.msg.connection
        if CHW.objects.filter(is_active=True, connection=connection):
            chw = CHW.objects.get(is_active=True, connection=connection)
            self.respond("Your phone is already registered to %s of %s health facility. Send HELP ACT if you need to be"
                         " assisted" % (chw.name, chw.location.name))
            return
        FlowCHWRegistration.objects.filter(connection=self.msg.connection).delete()
        FlowCHWRegistration.objects.create(connection=self.msg.connection, start_time=datetime.now(),
                                                       valid_until=datetime.now() + timedelta(hours=5))
        self.respond("Welcome to the ACT Program. To register as a CHW reply with your name.")

    def handle(self, text):
        self.help()