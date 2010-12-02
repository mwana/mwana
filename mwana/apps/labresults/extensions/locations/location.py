# vim: ai ts=4 sts=4 et sw=4

from django.db import models

class LocationLabResults(models.Model):
    send_live_results = models.BooleanField()

    class Meta:
        abstract = True
