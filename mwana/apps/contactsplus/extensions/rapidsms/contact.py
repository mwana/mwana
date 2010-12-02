# vim: ai ts=4 sts=4 et sw=4

from django.db import models

class ContactType(models.Model):
    
    types = models.ManyToManyField('contactsplus.ContactType',
                                   related_name='contacts', blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

