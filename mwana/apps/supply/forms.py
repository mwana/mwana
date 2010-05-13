from django import forms
from .models import *

class SupplyRequestForm(forms.ModelForm):
    
    class Meta:
        model = SupplyRequest
        fields = ("status",)
