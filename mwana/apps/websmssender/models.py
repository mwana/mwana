# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from rapidsms.models import Connection
import datetime


class WebSMSLog(models.Model):

    date_sent = models.DateTimeField(default=datetime.datetime.utcnow)
    sender = models.CharField(max_length=160)
    message = models.CharField(max_length=160)
    workertype = models.CharField(max_length=160)
    location = models.CharField(max_length=100)
    recipients_count = models.IntegerField()

    def __unicode__(self):
        return "%s sent a message on '%s' to %s people (%s)"  % (self.sender, self.date_sent, self.recipients_count, self.workertype)

class StagedMessage(models.Model):

    date = models.DateTimeField(default=datetime.datetime.utcnow)
    connection = models.ForeignKey(Connection)
    text = models.CharField(max_length=160)
    user = models.CharField(max_length=160)

    def __unicode__(self):
        return "Message created on '%s'"  % (self.date)
