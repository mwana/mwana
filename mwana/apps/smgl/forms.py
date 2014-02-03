import selectable.forms as selectable

from django import forms

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.help.models import HelpRequest
from mwana.apps.smgl.models import XFormKeywordHandler, Suggestion, FileUpload

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


class SMSRecordsFilterForm(StatisticsFilterForm):

    """
    A Form to filter SMS Records
    """
    keyword = forms.ModelChoiceField(
        queryset=XFormKeywordHandler.objects.all(),
        empty_label='(All)',
        required=False)


class SMSUsersFilterForm(StatisticsFilterForm):

    """
    A Form to filter SMS Users
    """
    c_type = forms.ModelChoiceField(queryset=ContactType.objects.all(),
                                    empty_label='(All)',
                                    required=False)

    status = forms.ChoiceField(choices=(
        ('', 'All'),
        ('active', 'Active'),
        ('inactive', 'Inactive')),
        required=False)

class ErrorFilterForm(SMSUsersFilterForm):
    class Meta:
        exclude = ('c_type')

class ANCReportForm(StatisticsFilterForm):
    filter_option = forms.ChoiceField(choices=(
        ('option_1', 'Option 1'),
        ('option_2', 'Option 2')
        ))

class ReportsFilterForm(SMSUsersFilterForm, ANCReportForm):
    pass

class SMSUsersSearchForm(forms.Form):

    """
    A Form to lookup SMS Users
    """
    search_string = forms.CharField(max_length=100, required=True)


class HelpRequestManagerForm(forms.ModelForm):

    """
    A Form to resolve Help Request
    """

    class Meta:
        model = HelpRequest
        fields = ('notes',)


class SuggestionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SuggestionForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['title'].widget.attrs['placeholder'] = 'Suggestion Title'

        self.fields['text'].widget.attrs['class'] = 'form-control'
        self.fields['closed'].widget.attrs['class'] = 'form-control'
        self.fields['close_comment'].widget.attrs['class'] = 'form-control'
        self.fields['text'].widget.attrs['placeholder'] = \
            'Describe your suggestion, you can add images/files below.'

    class Meta:
        model = Suggestion
        fields = ('title', 'text', 'closed', 'close_comment')


class FileUploadForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(FileUploadForm, self).__init__(*args, **kwargs)
        self.fields['file'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = FileUpload
        fields = ('file',)
