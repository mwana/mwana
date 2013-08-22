# vim: ai ts=4 sts=4 et sw=4
from django.forms.models import ModelForm
from django import forms
from mwana.apps.issuetracking.models import Issue, Comment

class IssueForm(ModelForm):
    
    desired_start_date = forms.DateField(required=False,
    widget=forms.TextInput(attrs={'class':'datefield'}))
    desired_completion_date = forms.DateField(required=False, label='Desired End Date',
    widget=forms.TextInput(attrs={'class':'datefield'}))
    dev_time = forms.CharField(max_length=160, required=False,
    widget=forms.TextInput(attrs={'placeholder': "e.g. 2 days, 3hours"}),
    label="Development time")

    class Meta:
        model = Issue
        exclude = ('assigned_to', 'start_date', 'end_date', 'percentage_complete'
        ,'status',)

class CommentForm(ModelForm):
    class Meta:
        model = Comment

