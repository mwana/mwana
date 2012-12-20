# vim: ai ts=4 sts=4 et sw=4

from django.db import models

class ContactRemindID(models.Model):
    remind_id = models.CharField(max_length=7, blank=True, null = True,
                     unique=True,
                     help_text="A unique id to trace patients through coc")

    class Meta:
        abstract = True

