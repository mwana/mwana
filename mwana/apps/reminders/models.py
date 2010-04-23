import datetime

from django.db import models

from rapidsms.models import Contact, Connection


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

    @property
    def possessive_pronoun(self):
        if not self.gender:
            return 'his or her'
        else:
            return self.gender == 'f' and 'her' or 'his'

    @property
    def pronoun(self):
        if not self.gender:
            return 'he or she'
        else:
            return self.gender == 'f' and 'she' or 'he'

    def __unicode__(self):
        return self.name


class Appointment(models.Model):
    """
    Followup appointment notifications to be sent to user
    """
    event = models.ForeignKey(Event, related_name='appointments')
    name = models.CharField(max_length=255)
    num_days = models.IntegerField(help_text='Number of days after the event '
                                   'this appointment should be. Reminders are '
                                   'sent two days before the appointment '
                                   'date.')
    
    def __unicode__(self):
        return self.name


class PatientEvent(models.Model):
    """
    Event that happened to a patient at a given time
    """
    patient = models.ForeignKey(Contact, related_name='patient_events')
    event = models.ForeignKey(Event, related_name='patient_events')
    cba_conn = models.ForeignKey(Connection, related_name='cba_patient_events')
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
    recipient = models.ForeignKey(Connection,
                                  related_name='sent_notifications')
    date_logged = models.DateTimeField()
    
    def __unicode__(self):
        return '%s sent to %s on %s' % (self.appointment,
                                        self.patient_event.patient,
                                        self.date_logged)
