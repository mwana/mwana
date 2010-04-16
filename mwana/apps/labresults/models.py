from django.db import models
from rapidsms.models import Connection

class Clinic(models.Model):
    clinic_id = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_fetch = models.DateField(null=True, blank=True)
    
class Result(models.Model):
    RESULT_CHOICES = (
        ('P', 'Positive'),
        ('N', 'Negative'),
        ('B', 'Bad Sample'),
    )

    STATUS_CHOICES = (
        ('in-transit', 'En route to lab'),
        ('unprocessed', 'At lab, not processed yet'),
        ('new', 'Fresh result from lab'),
        ('notified', 'Clinic notified of new result'),
        ('sent', 'Result sent to clinic'),
    )

    patient_id = models.CharField(max_length=30)
    sample_id = models.CharField(max_length=30)
    clinic_id = models.ForeignKey(Clinic)
    result = models.CharField(choices=RESULT_CHOICES, max_length=1)
    taken_on = models.DateField(null=True)
    entered_on = models.DateField()
    notification_status = models.CharField(choices=STATUS_CHOICES, max_length=15)

class Recipient(models.Model):
    connection = models.ForeignKey(Connection)
    clinic_id = models.ForeignKey(Clinic)
    pin = models.CharField(max_length=4)
    
