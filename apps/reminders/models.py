from django.db import models


class Language(models.Model):
    """
    A language, which can be used to link up message translations and
    recipients.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Message(models.Model):
    """
    An actual text message to be delivered to a user.  This is just a place
    holder model that all the translations of this message link to.
    """
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class MessageTranslation(models.Model):
    """
    A local language translation of a text message.
    """
    message = models.ForeignKey(Message, related_name='translations')
    language = models.ForeignKey(Language, related_name='message_translations')
    text = models.CharField(max_length=160)
    
    def __unicode__(self):
        return self.text[:40]
