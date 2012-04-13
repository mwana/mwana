from django.contrib import admin
from .models import XFormKeywordHandler

class XFormKeywordHandlerAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'function_path']

admin.site.register(XFormKeywordHandler, XFormKeywordHandlerAdmin)