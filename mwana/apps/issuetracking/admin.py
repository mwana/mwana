# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.issuetracking.models import Issue, Comment
from django.contrib import admin

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

class IssueAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'snippet' , 'type', 'status', 'priority',
    'assigned_to','author','start_date','end_date','date_created',)
    inlines = (CommentInline,)
    date_hierarchy = 'date_created'
    list_filter = ('type', 'status', 'assigned_to', 'web_author', 'sms_author',)
    search_fields = ('title', 'body',)


    def snippet(self, obj):
        if obj.body:
            return obj.body[0:50] + "..."

    def author(self, obj):
        if obj.sms_author:
            return obj.sms_author.name
        elif obj.web_author:
            return obj.web_author.username
        else:
            return "Unknown"

    def save_model(self, request, object, form, change):
        instance = form.save()
        if not instance.web_author and not instance.sms_author:
            instance.web_author = request.user
            
        instance.save()
        return instance

admin.site.register(Issue, IssueAdmin)
