import datetime

from django.db import models

from rapidsms.models import Contact


class Event(models.Model):
    """
    Anything that happens to a patient
    """
    GENDER_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    gender = models.CharField(max_length=1, blank=True, help_text='If this '
                              'event is gender-specific, specify the gender '
                              'here.', choices=GENDER_CHOICES)

    def __unicode__(self):
        return self.name


class Appointment(models.Model):
    """
    Followup appointment notifications to be sent to user
    """
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=255)
    num_days = models.IntegerField(help_text='Number of days after the event '
                                   'this appointment should be. Reminders are '
                                   'sent two days before the appointment '
                                   'date.')
    
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
    patient = models.ForeignKey(Patient, related_name='patient_events')
    event = models.ForeignKey(Event, related_name='patient_events')
    date = models.DateField()
    date_logged = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        self.date_logged = datetime.datetime.now()
        super(PatientEvent, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return '%s %s on %s' % (self.patient, self.event, self.date)


class SentNotification(models.Model):
    """
    Any notifications sent to user
    """
    appointment = models.ForeignKey(Appointment,
                                    related_name='sent_notifications')
    patient_event = models.ForeignKey(PatientEvent,
                                      related_name='sent_notifications')
    recipient = models.ForeignKey(Contact, related_name='sent_notifications')
    date_logged = models.DateTimeField()
    
    def __unicode__(self):
        return '%s sent to %s on %s' % (self.notification, self.patient,
                                        self.date)
