from django.db import models

from rapidsms.models import Contact


class Message(models.Model):
    """
    An actual text message to be delivered to a user.  This is just a place
    holder model that all the translations of this message link to.
    """
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=160)

    def __unicode__(self):
        return self.name


class Event(models.Model):
    """
    Anything that happens to a patient
    """
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    message = models.ForeignKey(Message, help_text='Acknowledgement message '
                                'sent to the contact person who creates this '
                                'event for a patient.')
    
    def __unicode__(self):
        return self.name


class Notification(models.Model):
    """
    Notifications to be sent to user
    """
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=255)
    num_days = models.IntegerField(help_text='Number of days after the event '
                                   'to send this notification.')
    message = models.ForeignKey(Message)
    
    def __unicode__(self):
        return self.name


class Patient(models.Model):
    """
    Patient details
    """
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    national_id = models.CharField(max_length=50, blank=True)
    
    def __unicode__(self):
        return self.name
 
 
class PatientEvent(models.Model):
    """
    Event that happened to a patient at a given time
    """
    patient = models.ForeignKey(Patient, related_name='patient_events')
    event = models.ForeignKey(Event, related_name='patient_events')
    date = models.DateField()
    date_logged = models.DateTimeField()
    
    def __unicode__(self):
        return '%s %s on %s' % (self.patient, self.event, self.date)
 

class SentNotification(models.Model):
    """
    Any notifications sent to user
    """
    notification = models.ForeignKey(Notification,
                                     related_name='sent_notifications')
    patient = models.ForeignKey(Patient, related_name='sent_notifications')
    recipient = models.ForeignKey(Contact, related_name='sent_notifications')
    date_logged = models.DateTimeField()
    
    def __unicode__(self):
        return '%s sent to %s on %s' % (self.notification, self.patient,
                                        self.date)
