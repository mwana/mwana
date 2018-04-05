# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import Client
from mwana.apps.act.models import CHW

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s


class StopACTMessagesHandler(KeywordHandler):
    """
    """

    keyword = "stop|444444"

    def help(self):
        self.handle('')

    def handle(self, text):
        exists = False
        for record in CHW.objects.filter(is_active=True, connection__identity=self.msg.connection.identity):
            record.is_active = False
            record.save()
            exists = True
        if exists:
            self.respond("You have successfully unsubscribed %(name)s.", name=record.name)
            return

        exists = False
        for record in Client.objects.filter(can_receive_messages=True, connection__identity=self.msg.connection.identity):
            record.can_receive_messages = False
            record.save()
            exists = True
        if exists:
            self.respond("You have successfully unsubscribed")
            return

        return True
