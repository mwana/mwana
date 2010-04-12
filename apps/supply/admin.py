from django.contrib import admin
from mwana.apps.supply.models import SupplyRequest, SupplyType

admin.site.register(SupplyRequest)
admin.site.register(SupplyType)