# vim: ai ts=4 sts=4 et sw=4
from rapidsms.messages.outgoing import OutgoingMessage
from datetime import datetime
import time

from mwana.apps.tlcprinters.models import MessageConfirmation

class TLCOutgoingMessage(OutgoingMessage):
    
    def send(self):
        # Pause a little. unit tests can run so fast such that 'sent_at' can be
        # equal for two different messages. Therefore, last_msg may not be as expected
        time.sleep(.1)
        try:
            last_msg = MessageConfirmation.objects.latest('sent_at')
        except MessageConfirmation.DoesNotExist:
            last_msg = None
#        seq_num = last_msg and last_msg.seq_num or -1 # this is a bug when last_msg.seq_num = 0. you will always get -1
        seq_num = last_msg.seq_num if (last_msg and (last_msg.seq_num!=None)) else -1
        if seq_num >= 255:
            seq_num = 0
        else:
            seq_num += 1
        seq_num_hex = '{0:02x}'.format(seq_num)
        if len(self._parts) > 0:
            template, kwargs = self._parts[0]
            self._parts[0] = (seq_num_hex + template, kwargs)
        else:
            self._parts.append(seq_num_hex, {})
        message_sent = super(TLCOutgoingMessage, self).send()
        if message_sent:
            MessageConfirmation.objects.create(connection=self._connection,
                                               text=self.text,
                                               sent_at=self.sent_at,
                                               seq_num=seq_num)
        else:
            MessageConfirmation.objects.create(connection=self._connection,
                                               text=self.text,
                                               sent_at=datetime.today(),
                                               seq_num=seq_num)
                                               