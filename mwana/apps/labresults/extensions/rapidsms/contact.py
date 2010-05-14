
from django.db import models

class ContactPin(models.Model):
    pin = models.CharField(max_length=4, blank=True,
                           help_text="A 4-digit security code for sms authentication workflows.")
    
    class Meta:
        abstract = True
