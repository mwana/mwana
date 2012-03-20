# vim: ai ts=4 sts=4 et sw=4
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
    slug = models.CharField(max_length=255, help_text='The keyword(s) to match '
                            'in messages from the user. Specify multiple '
                            'keywords by separating them with vertical bars, '
                            'e.g., "birth|bith|bilth"')
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
    STATUS_CHOICES = (
        ('new', 'New birth registered'),
        ('notified', 'Clinic notified of new birth'),
        ('sent', 'Birth details sent to clinic'),
        ('cooc', 'New continuum of care registered'),#set when server receives updates to a sample record
                                                #AFTER this result has already been sent to the clinic.
                                                #if result has not yet been sent, it keeps status 'new'.
                                                #the updated data may or may not merit sending the
                                                #update to the clinic (i.e., changed result, yes, changed
                                                #child age, no)
    )

    
    patient = models.ForeignKey(Contact, related_name='patient_events',
                                limit_choices_to={'types__slug': 'patient'})
    event = models.ForeignKey(Event, related_name='patient_events')
    cba_conn = models.ForeignKey(Connection, related_name='cba_patient_events',
                                 limit_choices_to={'contact__types__slug': 
                                          'cba'},verbose_name='CBA Connection')
    patient_conn = models.CharField(max_length=15, verbose_name='Patient Connection', null=True, blank=True)
    date = models.DateField()
    date_logged = models.DateTimeField()
    notification_status = models.CharField(choices=STATUS_CHOICES, max_length=15)   #New field added to accomodate birth notification status
    notification_sent_date = models.DateTimeField(null=True, blank=True)    #New field added to accomodate birth notification sent date
    
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.date_logged = datetime.datetime.now()
        super(PatientEvent, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return '%s %s on %s' % (self.patient.name, self.event, self.date)
    
    class Meta:
        unique_together = (('patient', 'event', 'date'),)


class SentNotification(models.Model):
    """
    Any notifications sent to user
    """
    appointment = models.ForeignKey(Appointment,
                                    related_name='sent_notifications')
    patient_event = models.ForeignKey(PatientEvent,
                                      related_name='sent_notifications')
    recipient = models.ForeignKey(Connection,
                                  related_name='sent_notifications',
                                  limit_choices_to={'contact__types__slug':
                                                                        'cba'})
    date_logged = models.DateTimeField()
    
    def __unicode__(self):
        return '%s sent to %s on %s' % (self.appointment,
                                        self.patient_event.patient,
                                        self.date_logged)
