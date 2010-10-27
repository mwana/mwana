from django.db import models

class LocPin(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    
    class Meta:
        abstract = True