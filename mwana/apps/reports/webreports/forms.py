# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from django.forms.models import ModelForm



class GroupFacilityMappingForm(ModelForm):

    class Meta:
        model = GroupFacilityMapping

class GroupUserMappingForm(ModelForm):

    class Meta:
        model = GroupUserMapping
        

