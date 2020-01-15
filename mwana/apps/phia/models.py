# vim: ai ts=4 sts=4 et sw=4
from django.db import models



class PhiaModel(models.Model):
    SEX_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )
    phone = models.CharField(max_length=13)
    sex = models.CharField(choices=SEX_CHOICES, max_length=1, blank=True, null=True)

