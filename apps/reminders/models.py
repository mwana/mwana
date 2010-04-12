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


class Event(models.Model):
    """
    Anything that happens to a patient
    """
    name = models.CharField(max_length=255)
    message = models.ForeignKey(Message)
    
    def __unicode__(self):
        return self.name


class Notification(models.Model):
    """
    Notifications to be sent to user
    """
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=255)
    num_days = models.IntegerField('Number of days after the event to send '
                                   'this notification')
    message = models.ForeignKey(Message)
    
    def __unicode__(self):
        return self.name
 
    
class Recipient(models.Model): 
    """
    Details of the message recipients
    """
    name = models.CharField(max_length=255)
    shortcut = models.CharField(max_length=255)
    language = models.ForeignKey(Language)
    number = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name


class Patient(models.Model):
    """
    Patient details
    """
    name = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
 
 
class PatientEvent(models.Model):
    """
    Event that happened to a patient at a given time
    """
    patient = models.ForeignKey(Patient)
    event = models.ForeignKey(Event)
    date = models.DateField()
    
    def __unicode__(self):
        return self.name
 

class SentNotification(models.Model):
    """
    Any notifications sent to user
    """
    notification = models.ForeignKey(Notification)
    patient = models.ForeignKey(Patient)
    recipient = models.ForeignKey(Recipient)
    date = models.DateField()
    
    def __unicode__(self):
        return self.name
