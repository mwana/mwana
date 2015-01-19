from django.conf import settings
from django import forms

import django_filters
# from django_filters import CharFilter, MultipleChoiceFilter
from mwana.apps.remindmi.filters import (MultiFieldFilter,
                                         MultipleChoiceMultiFieldFilter)

# from mwana.apps.remindmi.forms import DateFilterForm


from mwana.apps.emergency.models import FloodReport


DISTRICT_CHOICES = [(x, x) for x in settings.DISTRICTS]
EMPTY_CHOICE = ('', 'Any'),


class FloodFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        super(FloodFilter, self).__init__(*args, **kwargs)
        allow_empty = ['status']
        for field in allow_empty:
            self.filters[field].extra['choices'] = EMPTY_CHOICE + \
                                                   self.filters[field].extra['choices']

    startdate = django_filters.DateFilter(
        label="Reported from",
        lookup_type='gte',
        name='reported_on',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="Reported to",
        lookup_type='lte',
        name='reported_on',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['reported_by__contact__clinic__slug',
         'reported_by__contact__clinic__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['reported_by__contact__clinic__parent__parent__name',
         'reported_by__contact__clinic__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        model = FloodReport
        fields = ['status']
