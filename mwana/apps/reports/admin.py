# vim: ai ts=4 sts=4 et sw=4
from django.contrib.auth.models import User
from mwana.apps.reports.models import Login
from mwana.apps.reports.models import CbaEncouragement
from mwana.apps.reports.models import CbaThanksNotification
from django.contrib import admin
from mwana.apps.reports.models import *
from mwana.apps.reports.models import SupportedLocation
from mwana.apps.locations.models import Location
from django.contrib import admin
from django import forms


class TurnaroundAdmin(admin.ModelAdmin):
    list_display = ('district', 'facility', 'transporting', 'processing',
                    'delays', 'date_reached_moh', 'retrieving', 'date_retrieved',
                    'turnaround')
    date_hierarchy = 'date_retrieved'
    list_filter = ('date_retrieved', 'district', 'facility')
admin.site.register(Turnaround, TurnaroundAdmin)

class MessageGroupAdmin(admin.ModelAdmin):
    list_display = ('date', 'text', 'direction', 'contact_type',
                    'keyword', 'backend', 'changed_res',
                    'new_results', 'app', 'clinic', 'phone')
    date_hierarchy = 'date'
    list_filter = ('before_pilot','direction', 'contact_type', 'keyword', 'backend',
                   'new_results', 'changed_res','clinic', 'phone')
    search_fields = ('text', )
admin.site.register(MessageGroup, MessageGroupAdmin)
#admin.site.register(MessageGroup)



class SupportedLocationAdminForm(forms.ModelForm):
    class Meta:
        model = SupportedLocation

    def __init__(self, *args, **kwds):
        super(SupportedLocationAdminForm, self).__init__(*args, **kwds)
        self.fields['location'].queryset = Location.objects.order_by('name')



class SupportedLocationAdmin(admin.ModelAdmin):
    list_display = ('location', 'supported')
    list_filter = ('supported',)
    search_fields = ('location__name', 'location__slug',)
    form = SupportedLocationAdminForm
admin.site.register(SupportedLocation, SupportedLocationAdmin)



class PhoReportNotificationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'province', 'type', 'samples', 'results', 'births', 'date', 'date_sent')
    list_filter = ('province', 'date', 'date_sent')
    date_hierarchy = 'date_sent'
admin.site.register(PhoReportNotification, PhoReportNotificationAdmin)

class DhoReportNotificationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'district', 'type', 'samples', 'results', 'births', 'date', 'date_sent')
    list_filter = ('district', 'date', 'date_sent')
    date_hierarchy = 'date_sent'
admin.site.register(DhoReportNotification, DhoReportNotificationAdmin)

class CbaThanksNotificationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'facility', 'births', 'date', 'date_sent')
    list_filter = ('facility', 'date', 'date_sent')
    date_hierarchy = 'date_sent'
    search_fields = ('contact__name', )
admin.site.register(CbaThanksNotification, CbaThanksNotificationAdmin)

class CbaEncouragementAdmin(admin.ModelAdmin):
    list_display = ('contact', 'facility', 'date_sent')
    list_filter = ('facility', 'date_sent')
    date_hierarchy = 'date_sent'
    search_fields = ('contact__name', )
admin.site.register(CbaEncouragement, CbaEncouragementAdmin)

class LoginAdmin(admin.ModelAdmin):
    list_display = ('user', 'ever_logged_in',)
    list_filter = ('ever_logged_in',)
    search_fields = ('user__username', )
    list_editable = ('ever_logged_in',)

admin.site.register(Login, LoginAdmin)

admin.site.unregister(User)
class UserAdmin(admin.ModelAdmin):

    list_display = ('username', 'email', 'first_name', 'last_name',
    'last_login', 'days_ago', 'is_staff', 'partner_list',)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'last_login',)
    search_fields = ('username', 'email', 'first_name', 'last_name',)

    def partner_list(self, obj):
        return ', '.join(g.group.name for g in  obj.groupusermapping_set.all())

    def days_ago(self, obj):
        if obj.last_login:
            return (datetime.now() - obj.last_login).days

        return None

admin.site.register(User, UserAdmin)
