# # import operator

from django.conf import settings
# # from django.db.models import Q
from django import forms

import django_filters
# from django_filters import CharFilter, MultipleChoiceFilter
from mwana.apps.remindmi.filters import (MultiFieldFilter,
                                         MultipleChoiceMultiFieldFilter)

# from mwana.apps.remindmi.forms import DateFilterForm


from mwana.apps.labresults.models import Result


DISTRICT_CHOICES = [(x, x) for x in settings.DISTRICTS]
EMPTY_CHOICE = ('', 'Any'),


class ResultFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        super(ResultFilter, self).__init__(*args, **kwargs)
        allow_empty = ['result', 'notification_status', 'sex']
        for field in allow_empty:
            self.filters[field].extra['choices'] = EMPTY_CHOICE + \
                                                   self.filters[field].extra['choices']

    startdate = django_filters.DateFilter(
        label="Processed from",
        lookup_type='gte',
        name='processed_on',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="Processed to",
        lookup_type='lte',
        name='processed_on',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['clinic__slug', 'clinic__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['clinic__parent__parent__name', 'clinic__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)
    requisition_id = django_filters.CharFilter(label="Patient ID")
    clinic_care_no = django_filters.CharFilter(label="HCC Number")

    class Meta:
        # form = DateFilterForm
        model = Result
        fields = ['requisition_id', 'clinic_care_no', 'clinic',
                  'result', 'collected_on', 'processed_on',
                  'result_sent_date', 'notification_status', 'birthdate',
                  'child_age', 'sex', 'carer_phone']
