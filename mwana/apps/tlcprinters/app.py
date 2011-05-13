import logging
import rapidsms
import re
from django.conf import settings
from mwana.apps.tlcprinters.models import MessageConfirmation

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):
    confirm_regex = r'Confirm SMS:(.+)'
    
    def handle(self, message):
        """
        Handle the Confirm SMS messages sent by TLC printers.
        """
        match = re.match(self.confirm_regex, message.text, re.IGNORECASE)
        if not match:
            return False
        try:
            seq_num = int(match.group(1).strip(), 16)
        except ValueError:
            logger.warning('Received Confirm SMS message, but message ID %s'
                           'did not parse as hexadecimal.' % match.group(1))
            seq_num = None
        if seq_num:
            try:
                msg_conf = MessageConfirmation.objects.filter(
                                                              seq_num=seq_num,
                                                              connection=message.connection,
                                                              confirmed=False,
                                                              ).order_by('-sent_at')[0]
            except IndexError: #DoesNotExist never happens with filter()
                msg_conf = None
                logger.warning('No message confirmation found for '
                               'connection=%s and seq_num=%s' %
                               (message.connection, seq_num))
            if msg_conf:
                logger.debug('Marking message confirmation %s as confirmed' %
                             msg_conf)
                msg_conf.confirmed = True
                msg_conf.save()
        return True
