# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from rapidsms.models import Contact

from mwana.apps.locations.models import Location
from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.results_followup.models import EmailRecipientForInfantResultAlert
from mwana.apps.results_followup.models import InfantResultAlertViews
from mwana.apps.results_followup.models import InfantResultAlert


from django import forms


class InfantResultAlertAdminForm(forms.ModelForm):
    class Meta:
        model = InfantResultAlert

    def __init__(self, *args, **kwds):
        super(InfantResultAlertAdminForm, self).__init__(*args, **kwds)
        self.fields['referred_to'].queryset = Location.objects.exclude(type__slug__in=['zone', 'district', 'province']).order_by('name')


class InfantResultAlertAdmin(admin.ModelAdmin):
    def save_model(self, request, object, form, change):
        instance = form.save()
        instance.save()
        InfantResultAlertViews.objects.get_or_create(alert=instance, seen_by=request.user)
        return instance

    def queryset(self, request):
        user_groups = ReportingGroup.objects.filter(groupusermapping__user=
                                                    request.user).distinct()

        site_ids =  Location.objects.filter(groupfacilitymapping__group__in=
                                user_groups).distinct()

        return super(InfantResultAlertAdmin, self).queryset(request).filter(result__clinic__in=site_ids)

    list_display = ('location', 'clinic_staff', 'client_id', 'DOB_and_collected_on', 'followup_status',
                    'referred_to', 'treatment_start_date', 'notes'
                    )
    list_filter = ['followup_status', 'created_on',  'lab', 'sex', 'verified',
                   'collected_on', 'received_at_lab', 'processed_on', 'date_reached_moh', 'date_retrieved', 'location']
    search_fields = ('result__requisition_id', 'result__sample_id', 'location__name', 'notes')
    date_hierarchy = 'created_on'
    list_editable = ['followup_status', 'treatment_start_date', 'notes', ]
    form = InfantResultAlertAdminForm

    def client_id(self, obj):
        return "%s %s" % (obj.location.slug, obj.result.requisition_id)

    def clinic_staff(self, obj):
        return ", ".join ("%s %s" % (c.name, c.default_connection.identity) for c in Contact.active.filter(location=obj.result.clinic))
    def DOB_and_collected_on(self, obj):
        return "%s, %s " % (obj.birthdate, obj.collected_on)

admin.site.register(InfantResultAlert, InfantResultAlertAdmin)


class InfantResultAlertViewsAdmin(admin.ModelAdmin):
    list_display = ('alert', 'seen_by')
    list_filter = ['alert', 'seen_by']
admin.site.register(InfantResultAlertViews, InfantResultAlertViewsAdmin)


class EmailRecipientForInfantResultAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'last_alert_number', 'last_alert_date')
    list_filter = ['is_active', 'last_alert_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    list_editable = ['is_active']
    date_hierarchy = 'last_alert_date'
admin.site.register(EmailRecipientForInfantResultAlert, EmailRecipientForInfantResultAlertAdmin)
