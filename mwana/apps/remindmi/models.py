from django.db import models
from django.utils.translation import ugettext_lazy as _
from mwana.apps.appointments.models import Appointment
from mwana.apps.contactsplus.models import ContactType


class Message(models.Model):
    """
    A message to send to the user by type (healthworker or mother if opted in)
    """
    RECIPIENT_CHOICES = (
        ('hsa', 'Healthworker'),
        ('client', 'Mother'),
    )

    appointment = models.ForeignKey(Appointment, related_name='messages')
    name = models.CharField(max_length=255, null=True)
    content = models.TextField()
    recipient = models.ForeignKey(ContactType, related_name='recipients')

    def __unicode__(self):
        return self.name
