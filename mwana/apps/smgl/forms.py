import selectable.forms as selectable

from django import forms

from mwana.apps.contactsplus.models import ContactType

from .lookups import DistrictLookup, FacilityLookup, ProvinceLookup, ZoneLookup


class StatisticsFilterForm(forms.Form):
    """
    A form to filter National Statistics
    """
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    province = selectable.AutoCompleteSelectField(
        lookup_class=ProvinceLookup,
        label='Select a Province',
        required=False,
        widget=selectable.AutoComboboxSelectWidget
    )

    district = selectable.AutoCompleteSelectField(
        lookup_class=DistrictLookup,
        label='Select a District',
        required=False,
        widget=selectable.AutoComboboxSelectWidget
    )

    facility = selectable.AutoCompleteSelectField(
        lookup_class=FacilityLookup,
        label='Select a Facility',
        required=False,
        widget=selectable.AutoComboboxSelectWidget
    )

    def save(self, *args, **kwargs):
        return self.cleaned_data


class MotherSearchForm(forms.Form):
    """
    A Form to lookup mothers
    """
    uid = forms.CharField(max_length=100, required=True)


class MotherStatsFilterForm(StatisticsFilterForm):
    """
    A form to filter Mothers by various parameters
    """
    zone = selectable.AutoCompleteSelectField(
        lookup_class=ZoneLookup,
        label='Select a Zone',
        required=False,
        widget=selectable.AutoComboboxSelectWidget
    )

    edd_start_date = forms.DateField(required=False)
    edd_end_date = forms.DateField(required=False)

    def save(self, *args, **kwargs):
        return self.cleaned_data


class SMSUsersFilterForm(StatisticsFilterForm):
    """
    A Form to filter SMS Users
    """
    c_type = forms.ModelChoiceField(queryset=ContactType.objects.all(),
                                    empty_label='(All)',
                                    required=False)


class SMSUsersSearchForm(forms.Form):
    """
    A Form to lookup SMS Users
    """
    search_string = forms.CharField(max_length=100, required=True)
