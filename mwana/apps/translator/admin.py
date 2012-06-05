# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.translator.models import Dictionary
from mwana.apps.translator.models import Language
from django.contrib import admin



class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('slug', 'name',)

admin.site.register(Language, LanguageAdmin)


class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('language', 'key_phrase', 'translation',
    'alt_translations_one','alt_translations_two',)
    search_fields = ('language__name', 'language__slug', 'key_phrase', 'translation',)
admin.site.register(Dictionary, DictionaryAdmin)
