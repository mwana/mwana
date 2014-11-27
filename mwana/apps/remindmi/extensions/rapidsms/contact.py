# vim: ai ts=4 sts=4 et sw=4

from django.db import models


class ContactVolunteer(models.Model):
    volunteer = models.CharField(max_length=15, blank=True, null=True,
                                 help_text="Assigned volunteers number.")

    class Meta:
        abstract = True
