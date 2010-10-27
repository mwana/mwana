
from django.db import models

class ContactExtensions(models.Model):
    
    types = models.ManyToManyField('contactsplus.ContactType',
                                   related_name='contacts', blank=True)
    is_active = models.BooleanField(default=True)
    location = models.ForeignKey('locations.Location', null=True, blank=True,
                                 help_text="The location which this Contact "
                                 "last reported from.")

    class Meta:
        abstract = True
