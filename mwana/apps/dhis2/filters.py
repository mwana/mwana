# # import operator

from django.conf import settings
# # from django.db.models import Q
from django import forms

import django_filters
# from django_filters import CharFilter, MultipleChoiceFilter
from mwana.apps.remindmi.filters import (MultiFieldFilter,
                                         MultipleChoiceMultiFieldFilter)

# from mwana.apps.remindmi.forms import DateFilterForm


from mwana.apps.dhis2.models import Submission


DISTRICT_CHOICES = [(x, x) for x in settings.DISTRICTS]
EMPTY_CHOICE = ('', 'Any'),


class SubmissionFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        super(SubmissionFilter, self).__init__(*args, **kwargs)
        allow_empty = ['status']
        for field in allow_empty:
            self.filters[field].extra['choices'] = EMPTY_CHOICE + \
                                                   self.filters[field].extra['choices']

    startdate = django_filters.DateFilter(
        label="Date sent from",
        lookup_type='gte',
        name='date_sent',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="Date sent to",
        lookup_type='lte',
        name='date_sent',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['location__slug',
         'location__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['location__parent__parent__name',
         'location__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        model = Submission
        fields = ['indicator', 'date_sent', 'status']
