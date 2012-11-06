# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.blacklist.models import BlacklistedPeople
from django.contrib import admin



class BlacklistedPeopleAdmin(admin.ModelAdmin):
    list_display = ('phone','valid', 'date_created' , 'edited_on',)
    date_hierarchy = 'date_created'
    list_filter = ('phone','valid', 'date_created' , 'edited_on',)
    search_fields = ('phone',)


admin.site.register(BlacklistedPeople, BlacklistedPeopleAdmin)
