# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import datetime
from math import ceil
from datetime import timedelta
import string

from django.db import models
from django.db.models import Q
from mwana.apps.locations.models import Location
from mwana.const import CLINIC_SLUGS
from rapidsms.models import Contact

class ConfirmationCode(models.Model):
    def __unicode__(self):
        return str(self.id).zfill(6)

STOCK_TYPES = (
               ('drug', 'Drugs'),
               ('test_kit', 'Test Kits'),
               ('not_given', 'Not Given'),
               )


class StockUnit(models.Model):
    """
    Units used to measure Stock
    """
    abbr = models.CharField(max_length=10, null=True, blank=True)
    description = models.CharField(max_length=20, null=False, blank=False)

    def __unicode__(self):
        return "%s: %s" % (self.abr, self.description)


class Stock(models.Model):
    """
    Describes the type of Stock
    """

    type = models.CharField(max_length=10, choices=STOCK_TYPES, default='not_given')
    abbr = models.CharField(max_length=10, null=True, blank=True)
    code = models.CharField(max_length=10, null=False, blank=False, unique=True)
    short_code = models.CharField(max_length=10, null=False, blank=True, unique=True)
    name = models.CharField(max_length=80, null=False, blank=False)
    units = models.ForeignKey(StockUnit, null=True, blank=True)
    pack_size = models.CharField(max_length=15, null=True, blank=True)

    def __unicode__(self):
        return "%s: %s" % (self.code, self.name)

    def save(self, * args, ** kwargs):
        self.short_code = "".join(filter(lambda x:x in string.letters + string.digits, list(self.code)))
        super(Stock, self).save(*args, ** kwargs)


class StockOnHand(models.Model):
    date = models.DateField(default=datetime.now)
    facility = models.ForeignKey(Location)
    stock = models.ForeignKey(Stock)
    level = models.PositiveIntegerField()
    week_of_month = models.PositiveIntegerField(blank=True, null=True, editable=False)
    week_of_year = models.PositiveIntegerField(blank=True, null=True, editable=False)

    def __unicode__(self):
        return "; ".join(self.facility, self.stock, self.date.strftime('%d-%b-%Y'), self.level)

    def _week_of_month(self, dt):
        """ Returns the week of the month for the specified date.
            See http://stackoverflow.com/questions/3806473/python-week-number-of-the-month for comments
        """
        first_day = dt.replace(day=1)
        dom = dt.day
        adjusted_dom = dom + first_day.weekday()
        return int(ceil(adjusted_dom/7.0))

    def save(self, *args, **kwargs):
        if not self.date and not self.week_of_year:
            self.date = date.today()
            self.week_of_year = int(self.date.strftime('%U'))
        elif self.date and not self.week_of_year:
            self.week_of_year = int(self.date.strftime('%U'))

        if not self.date and not self.week_of_month:
            self.date = date.today()
            self.week_of_month = self._week_of_month(self.date)
        elif self.date and not self.week_of_month:
            self.week_of_month = self._week_of_month(self.date)

        super(StockOnHand, self).save(*args, **kwargs)


class Supported(models.Model):
    facility = models.ForeignKey(Location, related_name='supported_facilities',
                                limit_choices_to={'type__slug__in':CLINIC_SLUGS})
    supported = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s: %s" % (self.facility, "Supported" if self.supported else "Not Supported")

    class Meta:
        verbose_name_plural = "Supported"

