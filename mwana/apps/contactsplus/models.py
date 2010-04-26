from django.db import models


class ContactType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(unique=True, max_length=255)
    
    def __unicode__(self):
        return self.name
