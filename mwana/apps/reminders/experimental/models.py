# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.locations.models import Location
from datetime import datetime
from mwana.dateutils import week_start
from mwana.dateutils import weekend
from mwana.dateutils import week_of_year
from django.db import models

class SentNotificationToClinic(models.Model):
    """
    Event notifications sent to (supported) clinic users
    """
    location = models.ForeignKey(Location)
    event_name = models.CharField(max_length=10)
    number = models.PositiveSmallIntegerField()
    recipients = models.PositiveSmallIntegerField()
    date_logged = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return '%s %s sent to %s on %s' % (self.number, self.event_name, self.location,
                                        self.date_logged)
    def week(self):
        return "%s - (%s-%s)" % (week_of_year(self.date_logged),
                (week_start(self.date_logged)).strftime('%d %b'),
                (weekend(self.date_logged)).strftime('%d %b %Y'))

    class Meta:
        db_table = "reminders_sentnotificationtoclinic"


class Supported(models.Model):
    location =  models.ForeignKey(Location, limit_choices_to={'supportedlocation__supported':True})
    supported = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s" % self.location

    class Meta:
        verbose_name_plural = "Supported Sites"
        ordering = ["location__name",]
    