# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.backendtests.models import ForwardedMessage
from rapidsms.models import Contact

class ForwardedMessageAdmin(admin.ModelAdmin):
    list_display = ("connection", "date_sent", "responded", "date_responded", "response", "who", )
    list_filter = ("responded",)
    search_fields = ("text", 'connection__identity', )

    def who(self, obj):
        try:
            return Contact.active.get(connection__backend__name='message_tester',
                                      connection__identity=obj.connection.identity).name
        except:
            return ""
        
admin.site.register(ForwardedMessage, ForwardedMessageAdmin)




