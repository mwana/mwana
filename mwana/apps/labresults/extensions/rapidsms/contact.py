#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models

class ContactPin(models.Model):
    pin = models.CharField(max_length=4, blank=True,
                           help_text="A 4-digit security code for sms authentication workflows.")
    is_results_receiver = models.BooleanField\
                            (default=False,
                             help_text="Whether this person is allowed to receive lab results")

    class Meta:
        abstract = True
