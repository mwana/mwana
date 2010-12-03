# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from mwana.apps.locations.models import Location


class Hub(models.Model):
    name = models.CharField(max_length=50)
    district = models.ForeignKey(Location, unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return "%s in %s district. Contact: %s" % (self.name,
                                                   self.district.name,
                                                   self.phone)
class Lab(models.Model):
    source_key = models.CharField(max_length=50)
    name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return "%s. %s . Contact: %s" % (self.source_key, self.name, self.phone)
