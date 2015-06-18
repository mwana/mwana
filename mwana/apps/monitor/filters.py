from django.conf import settings
from django import forms

import django_filters
from mwana.apps.remindmi.filters import (MultiFieldFilter,
                                         MultipleChoiceMultiFieldFilter)


from mwana.apps.monitor.models import MonitorSample
# from .tables import FACS_DISTRICTS

EMPTY_CHOICE = [('', 'Any')]
# DISTRICTS_CHOICES = [(x, y) for FACS_DISTRICTS[1], ]

LAB_CHOICES = [('balaka/dream', 'Balaka/Dream'),
               ('lilongwe/pih', 'Lilongwe/PIH'),
               ('lilongwe/kch', 'Lilongwe/KCH'),
               ('blantyre/dream', 'Blantyre/Dream'),
               ('blantyre/queens', 'Blantyre/Queens'),
               ('mzimba/mdh', 'Mzimba/MDH'),
               ('mzuzu/central', 'Mzuzu/Central'),
               ('zomba/zch', 'Zomba/ZCH'),
]

STATUS_CHOICES = [('pending', 'Pending'),
                  ('synced', 'Synced')]

RESULT_CHOICES = [('all', 'All sites'), ('active', 'Active Sites'),
                  ('inactive', 'Inactive Sites')]


class MonitorSampleFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        super(MonitorSampleFilter, self).__init__(*args, **kwargs)
        allow_empty = ['status', 'lab_source']
        for field in allow_empty:
            self.filters[field].extra['choices'] = EMPTY_CHOICE + \
                                                   self.filters[field].extra['choices']


    startdate = django_filters.DateFilter(
        label="Start date",
        lookup_type='gte',
        name='result__processed_on',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="End date",
        lookup_type='lte',
        name='result__processed_on',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['hmis'],
        label="HMIS Code")
    lab_source = django_filters.ChoiceFilter(name='lab_source',
                                              label="Laboratory",
                                              choices=LAB_CHOICES)
    status = django_filters.ChoiceFilter(name='status', choices=STATUS_CHOICES)
    sample_id = django_filters.CharFilter(name='sample_id',
                                          label="Lab Sample ID")

    class Meta:
        model = MonitorSample
        fields = ['sample_id', 'hmis']


class ResultsDeliveryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(name='name')
    hmis = django_filters.AllValuesFilter(name='hmis')
    district = django_filters.AllValuesFilter(name='district')
    activity = django_filters.MethodFilter(action='location_activity',
    choices=RESULT_CHOICES)

    def location_activity(self, queryset, value):
        """
        Return locations with selected activity in LIMS.
        """
        if value == 'active':
            active = [i for i in queryset if i['num_lims'] > 0]
            return active
        elif value == 'inactive':
            inactive = [i for i in queryset if i['num_lims'] == 0]
            return inactive
        else:
            return queryset
