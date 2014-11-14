import operator

from django.conf import settings
from django.db.models import Q
from django import forms

import django_filters
from django_filters import CharFilter, MultipleChoiceFilter

from rapidsms.models import Contact

from mwana.apps.appointments.models import Appointment, Notification
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.labresults.models import EIDConfirmation
from mwana.apps.labresults.models import Result

from .forms import DateFilterForm


class MultiFieldFilter(CharFilter):
    """
    This filter preforms an OR query on the defined fields from a
    single entered value.
    The following will work similar to the default UserAdmin search::
    class UserFilterSet(FilterSet):
        search = MultiFieldFilter(['username', 'first_name',
                                 'last_name', 'email'])
        class Meta:
            model = User
            fields = ['search']
    """
    def __init__(self, fields, *args, **kwargs):
        super(MultiFieldFilter, self).__init__(*args, **kwargs)
        self.fields = fields
        self.lookup_type = 'icontains'
        self.lookup_types = [
            ('^', 'istartswith'),
            ('=', 'iexact'),
            ('@', 'search'),
        ]

    def filter(self, qs, value):
        if not self.fields or not value:
            return qs

        lookups = [self._get_lookup(str(field)) for field in self.fields]
        queries = [Q(**{lookup: value}) for lookup in lookups]
        qs = qs.filter(reduce(operator.or_, queries))
        return qs

    def _get_lookup(self, field_name):
        for key, lookup_type in self.lookup_types:
            if field_name.startswith(key):
                return "%s__%s" % (field_name[len(key):], lookup_type)
        return "%s__%s" % (field_name, self.lookup_type)


class MultipleChoiceMultiFieldFilter(MultipleChoiceFilter):
    """
    This filter preforms an OR query on the defined fields from a
    single entered value.
    The following will work similar to the default UserAdmin search::
    class UserFilterSet(FilterSet):
        search = MultipleChoiceMultiFieldFilter(['username', 'first_name',
                                 'last_name', 'email'])
        class Meta:
            model = User
            fields = ['search']
    """
    def __init__(self, fields, *args, **kwargs):
        super(MultipleChoiceFilter, self).__init__(*args, **kwargs)
        self.fields = fields
        self.lookup_type = 'icontains'
        self.lookup_types = [
            ('^', 'istartswith'),
            ('=', 'iexact'),
            ('@', 'search'),
        ]

    def filter(self, qs, value):
        if not self.fields or not value:
            return qs

        lookups = [self._get_lookup(str(field)) for field in self.fields]
        for v in value:
            queries = [Q(**{lookup: v}) for lookup in lookups]
        qs = qs.filter(reduce(operator.or_, queries))
        return qs

    def _get_lookup(self, field_name):
        for key, lookup_type in self.lookup_types:
            if field_name.startswith(key):
                return "%s__%s" % (field_name[len(key):], lookup_type)
        return "%s__%s" % (field_name, self.lookup_type)

DISTRICT_CHOICES = [(x, x) for x in settings.DISTRICTS]


class AppointmentFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(lookup_type='lt')
    hmis = MultiFieldFilter(
        ['subscription__connection__contact__location__slug',
         'subscription__connection__contact__location__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['subscription__connection__contact__location__parent__parent__name',
         'subscription__connection__contact__location__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        model = Appointment
        fields = ['date', 'hmis', 'districts', ]


class MothersListFilter(django_filters.FilterSet):
    class Meta:
        model = Contact


class PatientListFilter(django_filters.FilterSet):
    startdate = django_filters.DateFilter(
        label="Registered from",
        lookup_type='gte',
        name='created_on',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="Registered to",
        lookup_type='lte',
        name='created_on',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['location__slug', 'location__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['location__parent__parent__name', 'location__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        form = DateFilterForm
        model = Contact
        fields = ['hmis']


class ChildrenListFilter(PatientListFilter):
    pass


class PatientTraceFilter(django_filters.FilterSet):
    hmis = MultiFieldFilter(
        ['clinic__slug', 'clinic__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['clinic__parent__parent__name', 'clinic__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        model = PatientTrace
        fields = ['hmis', 'name', 'status']


class RemindersFilter(django_filters.FilterSet):
    hmis = MultiFieldFilter([
        'appointment__subscription__connection__contact__location__slug',
        'appointment__subscription__connection__contact__location__parent__slug']
    )
    districts = MultipleChoiceMultiFieldFilter(
        ['appointment__subscription__connection__contact__location__parent__parent__name',
         'appointment__subscription__connection__contact__location__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        model = Notification
        fields = ['hmis', 'districts', 'status']


class EIDConfirmationFilter(django_filters.FilterSet):
    class Meta:
        model = EIDConfirmation
        fields = ['result', 'contact', 'sample', 'status', 'art_number',
                  'age_in_months', 'action_taken', ]


class ResultFilter(django_filters.FilterSet):
    startdate = django_filters.DateFilter(
        label="Collected from",
        lookup_type='gte',
        name='collected_on',
        widget=forms.HiddenInput())
    enddate = django_filters.DateFilter(
        label="Collected to",
        lookup_type='lte',
        name='collected_on',
        widget=forms.HiddenInput())
    hmis = MultiFieldFilter(
        ['clinic__slug', 'clinic__parent__slug'],
        label="HMIS Code")
    districts = MultipleChoiceMultiFieldFilter(
        ['clinic__parent__parent__name', 'clinic__parent__name'],
        label="Districts", choices=DISTRICT_CHOICES)

    class Meta:
        # form = DateFilterForm
        model = Result
        fields = ['sample_id', 'requisition_id', 'clinic_care_no', 'clinic',
                  'result', 'collected_on', 'processed_on',
                  'result_sent_date', 'notification_status', 'birthdate',
                  'child_age', 'sex', 'carer_phone']
