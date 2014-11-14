from django import forms


class MwanaForm(forms.Form):
    date_of_birth = forms.DateField()
    mother_first_name = forms.CharField(max_length=30)
    mother_last_name = forms.CharField(max_length=30)
    child_first_name = forms.CharField(max_length=30)
    child_last_name = forms.CharField(max_length=30)
