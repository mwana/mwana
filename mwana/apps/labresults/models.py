from django.db import models
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection

    
class Result(models.Model):
    RESULT_CHOICES = (
        ('P', 'HIV Positive'),
        ('N', 'HIV Negative'),
        ('B', 'Bad Sample'),
    )

    STATUS_CHOICES = (
        ('in-transit', 'En route to lab'),
        ('unprocessed', 'At lab, not processed yet'),
        ('new', 'Fresh result from lab'),
        ('notified', 'Clinic notified of new result'),
        ('sent', 'Result sent to clinic'),
    )

    patient_id = models.CharField(max_length=30, blank=True)
    sample_id = models.CharField(max_length=30)
    clinic = models.ForeignKey(Location)
    result = models.CharField(choices=RESULT_CHOICES, max_length=1)
    taken_on = models.DateField(null=True)
    entered_on = models.DateField()
    notification_status = models.CharField(choices=STATUS_CHOICES, max_length=15)

    def __unicode__(self):
        return '%s/%s/%s %s (%s)' % (self.patient_id, self.sample_id, self.clinic.slug, self.result, self.notification_status)

