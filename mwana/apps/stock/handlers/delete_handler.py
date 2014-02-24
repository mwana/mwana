# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.stock.models import Transaction
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

_ = lambda s: s

UNREGISTERED = "Sorry, you must be registered first. Reply with HELP if you need assistance."
ALREADY_CANCELLED_TRANSACTION = "Your transaction with code %(code)s has already been cancelled."
UNKNOWN_TRANSACTION_MSG = _("Sorry, I don't think you did a stock transaction "
                            "with Confirmation code %(code)s. If you think this "
                            "message is a mistake reply with HELP")


class NewStockHandler(KeywordHandler):
    """
    """

    keyword = "delete|del|delite|delit"

    HELP_TEXT = _("To cancel a transaction, send DEL <CONFIRMATION_CODE>, E.g. DEL 000001")

    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond(UNREGISTERED)
            return True

        my_text = text.strip()
        if not my_text.isdigit():
            self.help()
            return True

        try:
            transaction = Transaction.objects.get(reference__id=int(my_text))
        except Transaction.DoesNotExist:
            self.respond(UNKNOWN_TRANSACTION_MSG, code=str(int(my_text)).zfill(6))
            return True

        if transaction.sms_user != self.msg.contact:
            self.respond(UNKNOWN_TRANSACTION_MSG, code=str(int(my_text)).zfill(6))
            return True

        if transaction.status == 'x':
            self.respond(ALREADY_CANCELLED_TRANSACTION, code=str(int(my_text)).zfill(6))
            return True

        affected = transaction.delete_transaction()        

        self.respond("Your transaction with code %s has been cancelled."
                     " New levels for the affected stock are: %s." %
                     (transaction.reference, ", ".join("%s units of %s" % (sa.amount, sa.stock.code) for sa in affected)))
