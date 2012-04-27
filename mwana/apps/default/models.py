from django.db import models

class DefaultResponse(models.Model):
    text = models.CharField(max_length=255)
    language = models.CharField(max_length=30)
