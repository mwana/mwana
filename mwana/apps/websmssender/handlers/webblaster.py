# vim: ai ts=4 sts=4 et sw=4
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages import OutgoingMessage
from mwana.apps.websmssender.models import StagedMessage


class Handler(KeywordHandler):

    keyword = "webblast"

    def help(self):
        self.respond("Error")

    def handle(self, text):
        if self.msg.connection.identity != "99999999":
            return
        for sm in StagedMessage.objects.filter(user=text.strip()):
            OutgoingMessage(sm.connection,sm.text).send()
        s = StagedMessage.objects.filter(user=text.strip())
        s.delete()
        return True
