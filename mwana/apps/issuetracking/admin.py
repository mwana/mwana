# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.issuetracking.models import Issue, Comment
from mwana.apps.issuetracking.utils import send_issue_email
from django.contrib import admin
import logging

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

class IssueAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'snippet' , 'type', 'status', 'dev_time',
    'assigned_to','author','desired_start_date', 'desired_completion_date','start_date','end_date',)
    inlines = (CommentInline,)
    date_hierarchy = 'date_created'
    list_filter = ('open', 'type', 'status', 'assigned_to', 'web_author', 'sms_author',)
    search_fields = ('title', 'body',)


    def snippet(self, obj):
        x = 500
        if obj.body:
            return obj.body[0:x] + ("..." if len(obj.body) > x else "")

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

        if instance.status in ['new', 'ongoing', 'resurfaced', 'future']:
            instance.open = True
        elif instance.status in ['completed', 'bugfixed', 'obsolete', 'closed']:
            instance.open = False

        if instance.status in ['completed', 'bugfixed']:
            instance.percentage_complete = 100

        instance.save()
        if instance.web_author and request.user:    
            try:
                send_issue_email(instance, request.user)
            except Exception, e:
                logger = logging.getLogger(__name__)
                logger.error(e)
        
        return instance


admin.site.register(Issue, IssueAdmin)
admin.site.register(Comment)
