from django.db import models

class Clinic(models.Model):
    clinic_id = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
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
    result = models.CharField(choices=RESULT_CHOICES)
    taken_on = models.DateField()
    entered_on = models.DateField()
    notification_status = models.CharField(choices=STATUS_CHOICES)

class Recipient(models.Model):
    connection = models.ForeignKey(Connection) #TODO #phone # of recipient
    clinic_id = models.ForeignKey(Clinic)
    pin = models.CharField(max_length=4)
    
