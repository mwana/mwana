from django.db import models

# Create your models here.


class XFormKeywordHandler(models.Model):
    keyword = models.CharField(max_length=255, help_text="The keyword that you want to associate with this handler.")
    function_path = models.CharField(max_length=255, help_text="The full path to the handler function. E.g: 'mwana.apps.smgl.app.birth_registration'")
