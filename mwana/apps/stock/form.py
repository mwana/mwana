# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.surveillance.models import Incident
from django.forms.models import ModelForm


class IncidentForm(ModelForm):

    class Meta:
        model = Incident
