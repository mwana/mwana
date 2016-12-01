# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.stockmini.models import Stock
from mwana.apps.stockmini.models import Supported
from mwana.apps.stockmini.models import StockUnit, StockOnHand


class StockUnitAdmin(admin.ModelAdmin):
    list_display = ('abbr', 'description')
    #list_filter = ['abbr', 'description']
    search_fields = ('abbr', 'description')
admin.site.register(StockUnit, StockUnitAdmin)


class StockOnHandAdmin(admin.ModelAdmin):
    list_display = ('date', 'facility', 'stock', 'level', 'week_of_month', 'week_of_year')
    list_filter = ['date', 'week_of_month', 'week_of_year', 'facility']
    search_fields = ('facility__name', 'stock__name')
    date_hierarchy = 'date'
admin.site.register(StockOnHand, StockOnHandAdmin)


class StockAdmin(admin.ModelAdmin):
    list_display = ('type', 'abbr', 'code', 'short_code', 'name', 'units')
    list_filter = ['type']
    search_fields = ('type', 'abbr', 'code', 'short_code', 'name')

admin.site.register(Stock, StockAdmin)


class SupportedAdmin(admin.ModelAdmin):
    list_display = ('facility', 'supported')
    list_filter = ['supported']
    search_fields = ('facility__name',)
    list_editable = ['supported']

admin.site.register(Supported, SupportedAdmin)