from django.contrib import admin
from mwana.apps.labresults.models import *

admin.site.register(Result)
admin.site.register(LabLog)
admin.site.register(Payload)
