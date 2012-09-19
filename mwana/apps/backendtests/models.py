# vim: ai ts=4 sts=4 et sw=4


from django.db import models
from rapidsms.models import Connection
from datetime import datetime

class ForwardedMessage(models.Model):
    connection = models.ForeignKey(Connection)
    date_sent = models.DateTimeField(default=datetime.now)
    date_responded = models.DateTimeField(null=True, blank=True)
    responded = models.BooleanField(default=False)
    response = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):        
        return "%s %s" % (self.connection, self.responded)
