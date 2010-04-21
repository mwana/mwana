#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models

class ContactZone(models.Model):
    zone_code = models.SmallIntegerField(blank=True, help_text="An optional "
                                         "code that indicates the zone"
                                         "in the catchment area of the "
                                         "contact's clinic for which he or "
                                         "she is responsible.")

    class Meta:
        abstract = True
