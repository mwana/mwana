from django.contrib import admin
from .models import XFormKeywordHandler, PreRegistration, PregnantMother, FacilityVisit

class XFormKeywordHandlerAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'function_path']

class PreRegsitrationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'has_confirmed', 'first_name', 'last_name', 'facility_name', 'facility_code', 'title', 'language']

class PregnantMotherAdmin(admin.ModelAdmin):
    list_display = ['uid', 'first_name', 'last_name', 'lmp', 'edd', 'next_visit']

class FacilityVisitAdmin(admin.ModelAdmin):
    list_display = ['location', 'mother', 'visit_date', 'next_visit', 'reason_for_visit']

admin.site.register(XFormKeywordHandler, XFormKeywordHandlerAdmin)
admin.site.register(PreRegistration, PreRegsitrationAdmin)
admin.site.register(PregnantMother, PregnantMotherAdmin)
admin.site.register(FacilityVisit, FacilityVisitAdmin)