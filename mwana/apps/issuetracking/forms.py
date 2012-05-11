# vim: ai ts=4 sts=4 et sw=4
from django.forms.models import ModelForm
from mwana.apps.issuetracking.models import Issue, Comment




class IssueForm(ModelForm):
    class Meta:
        model = Issue
        exclude = ('assigned_to', 'start_date', 'end_date',)

class CommentForm(ModelForm):
    class Meta:
        model = Comment

