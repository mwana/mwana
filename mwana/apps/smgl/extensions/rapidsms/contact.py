from django.db import models


class ContactLocation(models.Model):
    unique_id = models.CharField(max_length=255, blank=True, null=True, unique=True, 
                                 help_text="An optional Unique Identifier for this contact")

    class Meta:
        abstract = True
