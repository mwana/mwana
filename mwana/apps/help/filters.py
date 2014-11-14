# # import operator

from django.conf import settings
# # from django.db.models import Q
from django import forms

import django_filters
# from django_filters import CharFilter, MultipleChoiceFilter
from mwana.apps.remindmi.filters import (MultiFieldFilter,
                                         MultipleChoiceMultiFieldFilter)

# from mwana.apps.remindmi.forms import DateFilterForm


from mwana.apps.help.models import HelpRequest


DISTRICT_CHOICES = [(x, x) for x in settings.DISTRICTS]
EMPTY_CHOICE = ('', 'Any'),


class HelpFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        super(HelpFilter, self).__init__(*args, **kwargs)
        allow_empty = ['status']
        for field in allow_empty:
            self.filters[field].extra['choices'] = EMPTY_CHOICE + \
                                                   self.filters[field].extra['choices']

    startdate = django_filters.DateFilter(
        label="Requested from",
        lookup_type='gte',
        name='requested_on',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="Requestedsed to",
        lookup_type='lte',
        name='requested_on',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['requested_by__contact__clinic__slug',
         'requested_by__contact__clinic__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['requested_by__contact__clinic__parent__parent__name',
         'requested_by__contact__clinic__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        model = HelpRequest
        fields = ['requested_by', 'additional_text', 'status', 'addressed_on',
                  'resolved_by', 'notes']
