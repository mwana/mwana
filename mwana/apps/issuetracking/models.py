# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from rapidsms.models import Contact
from django.contrib.auth.models import User
from mwana.apps.issuetracking.utils import send_comment_email
import logging




class Issue(models.Model):

    TYPE_CHOICES = (
        ('feature', 'New Feature'),
        ('change', 'Change Request'),
        ('bug', 'Bug Fix'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),)

    STATUS_CHOICES = (
        ('new', 'Not Started'),
        ('ongoing', 'In Progress'),
        ('waiting', 'Waiting on Something'),
        ('completed', 'Completed'),
        ('bugfixed', 'Bug Fixed'),
        ('obsolete', 'Obsolete'),
        ('resurfaced', 'Resurfaced'),
        ('future', 'Future'),
        ('closed', 'Closed'),)

    PRIORITY_CHOICES = (
        ('high', 'High'),
        ('medium', 'Medium'),
        ('Low', 'Low'),)

    PERCENT_CHOICES =  tuple(zip(range(0, 101, 5), ( str(i)+"%" for i in range(0, 101, 5))))

    date_created = models.DateTimeField(auto_now_add=True, editable=False)    
    edited_on = models.DateTimeField(auto_now=True)
    type = models.CharField(choices=TYPE_CHOICES, max_length=15, blank=True)
    percentage_complete = models.PositiveIntegerField(choices=PERCENT_CHOICES,
    null=True, blank=True, default=0, verbose_name='% Complete')
    status = models.CharField(choices=STATUS_CHOICES, max_length=15, default='new')
    priority = models.CharField(choices=PRIORITY_CHOICES, max_length=7, default='medium')
    title = models.CharField(max_length=160)
    body = models.TextField(verbose_name='Description')
    sms_author = models.ForeignKey(Contact, null=True, blank=True, editable=False) #author
    web_author = models.ForeignKey(User, null=True, blank=True, editable=False) # author
    assigned_to = models.ForeignKey(User, null=True, blank=True,
                                    related_name="assigned_to",
                                    limit_choices_to={'is_active':'True', 'is_staff':'True'})
    start_date = models.DateField(null=True, blank=True, verbose_name='Actual Start Date')
    end_date = models.DateField(null=True, blank=True, verbose_name='Actual End Date')
    desired_start_date = models.DateField(null=True, blank=True)
    desired_completion_date = models.DateField(null=True, blank=True,  verbose_name='Desired End Date')
    open = models.NullBooleanField(null=True, blank=True, editable=False, default=True)
    dev_time = models.CharField(max_length=160, blank=True, null=True, verbose_name="Development time", help_text='e.g. 2days')

    def __unicode__(self):
        return self.title

    def assigned_to_full_name(self):
        f_name = ""
        if self.assigned_to and self.assigned_to.first_name:
            f_name = self.assigned_to.first_name
        l_name = ""
        if self.assigned_to and self.assigned_to.last_name:
            l_name = self.assigned_to.last_name
            
        return ("%s %s" % (f_name, l_name)).strip()

class Comment(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    edited_on = models.DateTimeField(auto_now=True)
    body = models.TextField()
    issue = models.ForeignKey(Issue)

    def save(self, *args, **kwargs):

        super(Comment, self).save(*args, **kwargs)
        
        if self.issue.web_author:
            try:
                send_comment_email(self)
            except Exception, e:
                logger = logging.getLogger(__name__)
                logger.error(e)

        

    def __unicode__(self):
        return "%s..." % self.body[0:50]

    class Meta:
            ordering = ["edited_on"]