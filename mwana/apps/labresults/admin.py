from django.contrib import admin
from mwana.apps.labresults.models import *

admin.site.register(Clinic)
admin.site.register(Recipient)
admin.site.register(Result)
admin.site.register(RawResult)
