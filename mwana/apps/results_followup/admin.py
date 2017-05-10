# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from rapidsms.models import Contact

from mwana.apps.results_followup.models import EmailRecipientForInfantResultAlert
from mwana.apps.results_followup.models import InfantResultAlertViews
from mwana.apps.results_followup.models import InfantResultAlert


class InfantResultAlertAdmin(admin.ModelAdmin):
    list_display = ('summary', 'followup_status', 'location', 'clinic_staff', 'birthdate',
                    'collected_on', 'processed_on',  'date_retrieved',
                    )
    list_filter = ['followup_status', 'notification_status', 'created_on',  'birthdate', 'sex', 'verified',
                   'collected_on', 'received_at_lab', 'processed_on', 'date_reached_moh', 'date_retrieved', 'location']
    search_fields = ('result__requisition_id', 'result__sample_id', 'location__name',)
    date_hierarchy = 'created_on'
    list_editable = ['followup_status']

    def summary(self, obj):
        return obj.__unicode__()

    def clinic_staff(self, obj):
        return ", ".join ("%s %s" % (c.name, c.default_connection.identity) for c in Contact.active.filter(location=obj.result.clinic))
admin.site.register(InfantResultAlert, InfantResultAlertAdmin)


class InfantResultAlertViewsAdmin(admin.ModelAdmin):
    list_display = ('alert', 'seen_by')
    list_filter = ['alert', 'seen_by']
admin.site.register(InfantResultAlertViews, InfantResultAlertViewsAdmin)


class EmailRecipientForInfantResultAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active')
    list_filter = ['is_active', 'user']
    list_editable = ['is_active']
admin.site.register(EmailRecipientForInfantResultAlert, EmailRecipientForInfantResultAlertAdmin)
