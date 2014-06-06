# vim: ai ts=4 sts=4 et sw=4
from mwana.const import DISTRICT_SLUGS
from mwana.apps.stock.models import Supported
from mwana.apps.stock.models import LowStockLevelNotification
from mwana.apps.stock.models import StockTransaction
from mwana.apps.locations.models import Location
from mwana.apps.stock.models import StockUnit
from mwana.apps.stock.models import Stock
from mwana.apps.stock.models import StockAccount
from mwana.apps.stock.models import Threshold
from mwana.apps.stock.models import Transaction
from django.contrib import admin
from django import forms

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('status', 'web_user', 'sms_user', 'date', 'reference', 'type')
    list_filter = ('status', 'type',  'date', )
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

class StockAccountAdminForm(forms.ModelForm):
    class Meta:
        model = StockAccount

    def __init__(self, *args, **kwds):
        super(StockAccountAdminForm, self).__init__(*args, **kwds)
        self.fields['location'].queryset = Location.objects.exclude(type__slug__in=['zone', 'district', 'province']).order_by('name')

class StockAccountAdmin(admin.ModelAdmin):
    list_display = ('stock', 'location', 'amount', 'last_updated')
    list_filter = ('stock', 'location',  'last_updated')
#    search_fields = ('stock', 'location', 'amount', 'last_updated')
    date_hierarchy = 'last_updated'
    form = StockAccountAdminForm

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

class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('amount', 'transaction', 'account_from', 'account_to', 'stock')
    list_filter = ('account_from',)
    #search_fields = ('amount', 'transaction', 'stock')

admin.site.register(StockTransaction, StockTransactionAdmin)


class LowStockLevelNotificationAdmin(admin.ModelAdmin):
    list_display = ('stock_account', 'contact', 'date_logged', 'week_of_year', 'level')
    list_filter = ('date_logged', 'contact', 'week_of_year')
    search_fields = ('stock_account__stock__code', 'stock_account__stock__name', 'contact__location__name',)
    date_hierarchy = 'date_logged'

admin.site.register(LowStockLevelNotification, LowStockLevelNotificationAdmin)

class SupportedAdminForm(forms.ModelForm):
    class Meta:
        model = Supported

    def __init__(self, *args, **kwds):
        super(SupportedAdminForm, self).__init__(*args, **kwds)
        self.fields['district'].queryset = Location.objects.filter(type__slug__in=DISTRICT_SLUGS).order_by('name')

class SupportedAdmin(admin.ModelAdmin):
    list_display = ('district', 'supported')
    list_filter = ('district', 'supported')
    #search_fields = ('district', 'supported')
    list_editable = ('supported',)
    form = SupportedAdminForm

admin.site.register(Supported, SupportedAdmin)
