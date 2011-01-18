from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.tlcprinters.models import MessageConfirmation

class TLCOutgoingMessage(OutgoingMessage):
    
    def send(self):
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
