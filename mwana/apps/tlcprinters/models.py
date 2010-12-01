from django.db import models

from rapidsms import models as rapidsms


class MessageConfirmation(models.Model):
    connection = models.ForeignKey(rapidsms.Connection)
    sent_at = models.DateTimeField()
    text = models.CharField(max_length=160)
    seq_num = models.SmallIntegerField()
    confirmed = models.BooleanField(default=False)

    def __unicode__(self):
        return '{conn}: {msg} (confirmed={confirmed})'.format(msg=self.text,
                                                      conn=self.connection,
                                                      confirmed=self.confirmed)
