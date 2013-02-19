# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.training.models import Trained
from django.forms.models import ModelForm



class TrainedForm(ModelForm):

    class Meta:
        model = Trained


        

