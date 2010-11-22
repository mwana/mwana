
from django.db import models

class ContactPin(models.Model):
    pin = models.CharField(max_length=4, blank=True,
                           help_text="A 4-digit pin code for sms authentication workflows.")
    alias = models.CharField(max_length=100)
    
    class Meta:
        abstract = True
