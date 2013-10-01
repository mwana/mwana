# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.stock.models import StockUnit
from mwana.apps.stock.models import Stock
from mwana.apps.stock.models import StockAccount
from mwana.apps.stock.models import Threshold
from mwana.apps.stock.models import Transaction
from django.contrib import admin

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('status', 'web_user', 'sms_user', 'account_from', 'account_to', 'date', 'reference', 'type')
    list_filter = ('status', 'type',  'date', 'account_from', 'account_to', )
    search_fields = ('web_user__name', 'sms_user__name', 'reference')
    date_hierarchy = 'date'

    def save_model(self, request, object, form, change):
        instance = form.save()
        if not instance.web_user and not instance.sms_user:
            instance.web_user = request.user

        instance.save()

        return instance

admin.site.register(Transaction, TransactionAdmin)

class ThresholdAdmin(admin.ModelAdmin):
    list_display = ('account', 'level', 'start_date', 'end_date')
    list_filter = ('account', 'level', 'start_date', 'end_date')
    #search_fields = ('account', 'level', 'start_date', 'end_date')
    date_hierarchy = 'start_date'

admin.site.register(Threshold, ThresholdAdmin)

class StockAccountAdmin(admin.ModelAdmin):
    list_display = ('stock', 'location', 'amount', 'last_updated')
    list_filter = ('stock', 'location',  'last_updated')
    #search_fields = ('stock', 'location', 'amount', 'last_updated')
    date_hierarchy = 'last_updated'

admin.site.register(StockAccount, StockAccountAdmin)

class StockAdmin(admin.ModelAdmin):
    list_display = ('type', 'abbr', 'code', 'name', 'units')
    list_filter = ('type', 'units')
    search_fields = ('abbr', 'code', 'name',)

admin.site.register(Stock, StockAdmin)


class StockUnitAdmin(admin.ModelAdmin):
    list_display = ('abbr', 'description')
    search_fields = ('abbr', 'description')

admin.site.register(StockUnit, StockUnitAdmin)






