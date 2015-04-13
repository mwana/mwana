from django.conf import settings
from django import forms

import django_filters
from mwana.apps.remindmi.filters import (MultiFieldFilter,
                                         MultipleChoiceMultiFieldFilter)


from mwana.apps.monitor.models import MonitorSample
from .tables import FACS_DISTRICTS

EMPTY_CHOICE = ('', 'Any'),
# DISTRICTS_CHOICES = [(x, y) for FACS_DISTRICTS[1], ]

class MonitorSampleFilter(django_filters.FilterSet):

    startdate = django_filters.DateFilter(
        label="Start date",
        lookup_type='gte',
        name='payload__incoming_date',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="End date",
        lookup_type='lte',
        name='payload__incoming_date',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['hmis'],
        label="HMIS Code")
    lab_source = django_filters.AllValuesFilter(name='payload__source',
                                      label="Laboratory")
    status =django_filters.AllValuesFilter(name='status')
    sample_id = django_filters.CharFilter(name='sample_id', label="Lab Sample ID")

    class Meta:
        model = MonitorSample
        fields = ['sample_id', 'hmis']


class ResultsDeliveryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(name='name')
    hmis = django_filters.AllValuesFilter(name='hmis')
    district = django_filters.AllValuesFilter(name='district')
