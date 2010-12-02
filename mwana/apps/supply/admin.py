# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.supply.models import SupplyRequest, SupplyType

admin.site.register(SupplyRequest)
admin.site.register(SupplyType)