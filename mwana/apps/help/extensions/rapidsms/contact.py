# vim: ai ts=4 sts=4 et sw=4

from django.db import models

class ContactHelp(models.Model):
    
    is_help_admin= models.BooleanField\
                    (default=False,
                     help_text="Whether this person should be notified when there are help requests.")

    class Meta:
        abstract = True
