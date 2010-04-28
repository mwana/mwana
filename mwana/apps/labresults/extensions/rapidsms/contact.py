#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models

class ContactPin(models.Model):
    pin = models.CharField(max_length=4, blank=True,
                           help_text="A 4-digit security code for sms authentication workflows.")
    
    class Meta:
        abstract = True
