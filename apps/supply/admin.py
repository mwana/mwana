from django.contrib import admin
from .models import SupplyRequest, SupplyType

admin.site.register(SupplyRequest)
admin.site.register(SupplyType)