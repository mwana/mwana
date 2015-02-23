# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.models import ScaleUpSite
from mwana.apps.reports.models import MessageByLocationByBackend
from mwana.apps.reports.models import MessageByLocationByUserType
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

from django.db import transaction
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AdminPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.html import escape
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect


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
        self.fields['location'].queryset = Location.objects.exclude(type__slug='zone').order_by('name')



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

csrf_protect_m = method_decorator(csrf_protect)

class GroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('permissions',)

class UserAdmin(admin.ModelAdmin):
    add_form_template = 'admin/auth/user/add_form.html'
    change_user_password_template = None
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')}
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('username', 'email', 'first_name', 'last_name',
    'last_login', 'days_ago', 'is_staff', 'partner_groups',)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'last_login',)
    search_fields = ('username', 'email', 'first_name', 'last_name',
    'groupusermapping__group__name',)
    ordering = ('username',)
    filter_horizontal = ('user_permissions',)
    
    def partner_groups(self, obj):
        return ', '.join(g.group.name for g in  obj.groupusermapping_set.all())

    def days_ago(self, obj):
        if obj.last_login:
            return (datetime.now() - obj.last_login).days

        return None



    def __call__(self, request, url):
        # this should not be here, but must be due to the way __call__ routes
        # in ModelAdmin.
        if url is None:
            return self.changelist_view(request)
        if url.endswith('password'):
            return self.user_change_password(request, url.split('/')[0])
        return super(UserAdmin, self).__call__(request, url)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(UserAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults.update({
                'form': self.add_form,
                'fields': admin.util.flatten_fieldsets(self.add_fieldsets),
            })
        defaults.update(kwargs)
        return super(UserAdmin, self).get_form(request, obj, **defaults)

    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
            (r'^(\d+)/password/$', self.admin_site.admin_view(self.user_change_password))
        ) + super(UserAdmin, self).get_urls()

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(request):
            if self.has_add_permission(request) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404('Your user does not have the "Change user" permission. In order to add users, Django requires that your user account have both the "Add user" and "Change user" permissions set.')
            raise PermissionDenied
        if extra_context is None:
            extra_context = {}
        defaults = {
            'auto_populated_fields': (),
            'username_help_text': self.model._meta.get_field('username').help_text,
        }
        extra_context.update(defaults)
        return super(UserAdmin, self).add_view(request, form_url, extra_context)

    def user_change_password(self, request, id):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = get_object_or_404(self.model, pk=id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                new_user = form.save()
                msg = ugettext('Password changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': form.base_fields.keys()})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        return render_to_response(self.change_user_password_template or 'admin/auth/user/change_password.html', {
            'title': _('Change password: %s') % escape(user.username),
            'adminForm': adminForm,
            'form': form,
            'is_popup': '_popup' in request.REQUEST,
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
            'root_path': self.admin_site.root_path,
        }, context_instance=RequestContext(request))

admin.site.register(User, UserAdmin)


class MessageByLocationByUserTypeAdmin(admin.ModelAdmin):
    list_display = ('province', 'district', 'facility', 'worker_type', 'year',
    'month', 'province_slug', 'district_slug', 'facility_slug',
    'absolute_location', 'count', 'count_incoming','count_outgoing', 'min_date','max_date', "month_year")
    list_filter = ('worker_type', 'year', 'month', 'province', 'district', 'facility', 'province_slug', 'district_slug', 'facility_slug', )
#    search_fields = ('count', 'province', 'district', 'facility', 'worker_type', 'year', 'month', 'province_slug', 'district_slug', 'facility_slug',)

admin.site.register(MessageByLocationByUserType, MessageByLocationByUserTypeAdmin)

class MessageByLocationByBackendAdmin(admin.ModelAdmin):
    list_display = ('count', 'province', 'district', 'facility', 'backend', 'year', 'month', 'province_slug', 'district_slug', 'facility_slug', 'absolute_location', 'min_date', 'max_date', 'month_year', 'count_incoming', 'count_outgoing')
    list_filter = ('backend', 'year', 'month', 'province', 'district', 'facility')
    #search_fields = ('count', 'province', 'district', 'facility', 'backend', 'year', 'month', 'province_slug', 'district_slug', 'facility_slug', 'absolute_location', 'min_date', 'max_date', 'month_year', 'count_incoming', 'count_outgoing')
    date_hierarchy = 'min_date'

admin.site.register(MessageByLocationByBackend, MessageByLocationByBackendAdmin)


class ScaleUpSiteAdmin(admin.ModelAdmin):
    list_display = ('province', 'district', 'site', 'PMTCT', 'EID', 'ART', 'PaedsART', 'Mwana', 'ActiveOnMwana')
    list_filter = ('PMTCT', 'EID', 'ART', 'PaedsART', 'Mwana', 'ActiveOnMwana', 'province', 'district', 'site',)
    search_fields = ('province', 'district', 'site__name')
    list_editable = ('PMTCT', 'EID', 'ART', 'PaedsART',)
admin.site.register(ScaleUpSite, ScaleUpSiteAdmin)


class ClinicsNotSendingDBSAdmin(admin.ModelAdmin):
    list_display = ('location', 'last_sent_samples', 'last_retrieved_results', 'last_used_sent', 'last_used_check', 'last_used_result', 'last_modified', 'contacts')
    list_filter = ('location', )
    search_fields = ('contacts',)

admin.site.register(ClinicsNotSendingDBS, ClinicsNotSendingDBSAdmin)
