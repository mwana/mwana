# vim: ai ts=4 sts=4 et sw=4
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages import OutgoingMessage
from mwana.apps.websmssender.models import StagedMessage


class Handler(KeywordHandler):

    keyword = "blast2"

    def help(self):
        self.respond("Error")

    def handle(self, text):
        for sm in StagedMessage.objects.all():
            OutgoingMessage(sm.connection,sm.text).send()
            sm.delete()
            sm.save()
        return True
