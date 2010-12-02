# vim: ai ts=4 sts=4 et sw=4
from django import forms
from .models import *

class SupplyRequestForm(forms.ModelForm):
    
    class Meta:
        model = SupplyRequest
        fields = ("status",)
