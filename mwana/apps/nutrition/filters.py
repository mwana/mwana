# # import operator

from django.conf import settings
# # from django.db.models import Q
from django import forms

import django_filters
# from django_filters import CharFilter, MultipleChoiceFilter
from mwana.apps.remindmi.filters import (MultiFieldFilter,
                                         MultipleChoiceMultiFieldFilter)

# from mwana.apps.remindmi.forms import DateFilterForm


from mwana.apps.nutrition.models import Assessment


DISTRICT_CHOICES = [(x, x) for x in settings.DISTRICTS]
EMPTY_CHOICE = ('', 'Any'),


class AssessmentFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        super(AssessmentFilter, self).__init__(*args, **kwargs)
        allow_empty = ['status', 'underweight', 'stunting', 'wasting',
                       'action_taken']
        for field in allow_empty:
            self.filters[field].extra['choices'] = EMPTY_CHOICE + \
                                                   self.filters[field].extra['choices']

    startdate = django_filters.DateFilter(
        label="Reported from",
        lookup_type='gte',
        name='date',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="Reported to",
        lookup_type='lte',
        name='date',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['healthworker__clinic__slug',
         'healthworker__clinic__name',
         'healthworker__clinic__parent__slug',
         'healthworker__clinic__parent__name'],
        label="HMIS Code/Name")
    districts = MultipleChoiceMultiFieldFilter(
        ['healthworker__clinic__parent__parent__name',
         'healthworker__clinic__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        model = Assessment
        fields = ['healthworker', 'status', 'muac', 'oedema', 'underweight',
                  'stunting', 'wasting', 'action_taken']
