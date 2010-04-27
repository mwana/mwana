from django.db import models

from rapidsms.models import Contact


class ContactType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name