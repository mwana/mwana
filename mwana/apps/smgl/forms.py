from django import forms

import selectable.forms as selectable

from mwana.apps.locations.models import Location

from .lookups import DistrictLookup


class NationalStatisticsFilterForm(forms.Form):
    """
    A form to filter National Statistics
    """

    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    province = forms.ModelChoiceField(queryset=Location.objects.filter(
                                                    type__singular='Province'
                                                    ),
                                     empty_label='All Provinces',
                                     required=False,)

    district = selectable.AutoCompleteSelectField(
        lookup_class=DistrictLookup,
        label='Select a District',
        required=False,
        widget=selectable.AutoComboboxSelectWidget
    )

    def save(self, *args, **kwargs):
        return self.cleaned_data


class DistrictStatisticsFilterForm(NationalStatisticsFilterForm):
    """
    A form to filter District Statistics
    """
    def __init__(self, *args, **kwargs):
        super(DistrictStatisticsFilterForm, self).__init__(*args, **kwargs)
        self.facilties = Location.objects.exclude(type)

    facility = forms.ModelChoiceField(queryset=Location.objects.filter(
                                            type__singular__in='district'
                                                    ),
                                     empty_label='All Facilities',
                                     required=False,)
