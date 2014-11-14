from django.conf import settings
from django import forms


class SomeForm(forms.Form):
    CHOICES = tuple([(d, d) for d in settings.DISTRICTS])
    picked = forms.MultipleChoiceField(
        choices=CHOICES,
        widget=forms.SelectMultiple())
