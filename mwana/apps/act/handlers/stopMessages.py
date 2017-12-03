# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import CHW

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s


class StopACTMessagesHandler(KeywordHandler):
    """
    """

    keyword = "stop|444444|44444|4444|444"

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

#        exists = False
#        # we should idealy expect one such record
#        for record in Client.objects.filter(is_active=True, connection__identity=self.msg.connection.identity):
#            record.is_active = False
#            record.save()
#            WaitingForResponse.objects.create(client_gestation=record)
#            exists = True
#        if exists:
#            self.respond("You have successfully unsubscribed. Please let us know why. "
#                         "Send 1 for Pregnancy ended"
#                         "\n2 for Baby was still-born"
#                         "\n3 for Do not want reminders")
#            return
#        else:
#            # TODO: deactivate if CHW
#            self.respond("Thank you for your submission to stop receiving messages")
        return True
