# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.phia.models import Linkage
from mwana.apps.phia.models import Followup
from django.contrib import admin
from mwana.apps.phia.models import *

class LabLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'message', 'level', 'line','source',)
    list_filter = ('timestamp', 'level')
    search_fields = ('message', 'payload__source')

    def source(self, obj):
        return obj.payload.source

admin.site.register(LabLog, LabLogAdmin)


class PayloadAdmin(admin.ModelAdmin):
    list_display = ('incoming_date', 'auth_user', 'version', 'source',
                    'client_timestamp', 'info', 'parsed_json',
                    'validated_schema')
    list_filter = ('incoming_date',  'source', 'version',
                   'parsed_json', 'validated_schema',)
    search_fields = ('raw',)

admin.site.register(Payload, PayloadAdmin)

from django.contrib import admin

class ResultAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'requisition_id', 'sex', 'age', 'send_pii', 
    'share_contact', 'contact_by_phone', 'fa_code', 'fa_name', 'contact_method',
    'clinic', 
    'result_detail', 'collected_on', 'entered_on', 'processed_on', 
    'notification_status', 'birthdate', 'age', 'age_unit', 
   
  'verified', 'result_sent_date', 
  
   
    'past_test', 'past_status', 'new_status', 'was_on_art', 'on_art', 'art_start_date',
    'contact_by_phone', 'send_pii', 'share_contact',
    'bd_date', 'vl', 'vl_date', 'cd4', 'cd4_date')
    #list_filter = ['sex', 'age', 'send_pii', 'share_contact', 'contact_by_phone', 'fa_code', 'fa_name', 'contact_method', 'sample_id', 'requisition_id', 'payload', 'clinic', 'related_name', 'clinic_code_unrec', 'blank', 'given_facility_name', 'blank', 'given_facility_code', 'blank', 'result_detail', 'collected_on', 'entered_on', 'processed_on', 'notification_status', 'birthdate', 'age', 'age_unit', 'collecting_health_worker', 'coll_hw_title', 'record_change', 'old_value', 'verified', 'result_sent_date', 'date_of_first_notification', 'arrival_date', 'phone_invalid', 'province', 'district', 'date_clinic_notified', 'date_participant_notified', 'who_retrieved', 'related_name', 'participant_informed', 'past_test', 'past_status', 'new_status', 'was_on_art', 'on_art', 'art_start_date', 'contact_by_phone', 'send_pii', 'share_contact', 'contact_method', 'bd_date', 'vl', 'vl_date', 'cd4', 'cd4_date']
    #search_fields = ('sex', 'age', 'send_pii', 'share_contact', 'contact_by_phone', 'fa_code', 'fa_name', 'contact_method', 'sample_id', 'requisition_id', 'payload', 'clinic', 'related_name', 'clinic_code_unrec', 'blank', 'given_facility_name', 'blank', 'given_facility_code', 'blank', 'result_detail', 'collected_on', 'entered_on', 'processed_on', 'notification_status', 'birthdate', 'age', 'age_unit', 'collecting_health_worker', 'coll_hw_title', 'record_change', 'old_value', 'verified', 'result_sent_date', 'date_of_first_notification', 'arrival_date', 'phone_invalid', 'province', 'district', 'date_clinic_notified', 'date_participant_notified', 'who_retrieved', 'related_name', 'participant_informed', 'past_test', 'past_status', 'new_status', 'was_on_art', 'on_art', 'art_start_date', 'contact_by_phone', 'send_pii', 'share_contact', 'contact_method', 'bd_date', 'vl', 'vl_date', 'cd4', 'cd4_date')
    date_hierarchy = 'arrival_date'    
admin.site.register(Result, ResultAdmin)


class FollowupAdmin(admin.ModelAdmin):
    list_display = ('temp_id', 'clinic_name', 'reported_on', 'reported_by', 'result')
    list_filter = ['reported_on', 'reported_by', 'clinic_name',]
    search_fields = ('temp_id', 'clinic_name', 'reported_by')
    date_hierarchy = 'reported_on'
admin.site.register(Followup, FollowupAdmin)


class LinkageAdmin(admin.ModelAdmin):
    list_display = ('temp_id', 'clinic', 'clinic_code', 'linked_by', 'linked_on', 'result')
    list_filter = ['linked_by', 'clinic',]
    search_fields = ('temp_id', 'clinic_code', 'result')
    date_hierarchy = 'linked_on'
admin.site.register(Linkage, LinkageAdmin)
