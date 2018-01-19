# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.models import VerifiedNumber
from mwana.apps.act.models import Client
from mwana.apps.act.models import CHW

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


_ = lambda s: s


class ActYesHandler(KeywordHandler):
    """
    """

    keyword = "act yes|actyes|act yes.|actyes.|act confirm"
    
    HELP_TEXT = _("To confirm your number send ACT YES")
    
    def help(self):
        self.handle("")

    def handle(self, text):
        phone_number = self.msg.connection.identity
        short_phone_number = phone_number[-10:]
        verified, _ = VerifiedNumber.objects.get_or_create(number=phone_number)
        verified.verified = True
        verified.save()

        if CHW.objects.filter(phone__endswith=short_phone_number):
            for rec in CHW.objects.filter(phone__endswith=short_phone_number):
                rec.phone_verified = True
                rec.connection = self.msg.connection
                rec.save()

        if Client.objects.filter(phone__endswith=short_phone_number):
            for rec in Client.objects.filter(phone__endswith=short_phone_number):
                rec.phone_verified = True
                rec.connection = self.msg.connection
                rec.save()

        self.respond("Thank you")
        return True