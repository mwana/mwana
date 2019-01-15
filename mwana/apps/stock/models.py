# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import datetime
from datetime import timedelta
import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from mwana.apps.locations.models import Location
from mwana.const import DISTRICT_SLUGS
from mwana.const import CLINIC_SLUGS
from rapidsms.models import Contact

class ConfirmationCode(models.Model):
    def __unicode__(self):
        return str(self.id).zfill(6)

STOCK_TYPES = (
               ('drug', 'Drugs'),
               ('test_kit', 'Test Kits'),
               )


class StockUnit(models.Model):
    """
    Units used to measure Stock
    """
    abbr = models.CharField(max_length=10, null=True, blank=True)
    description = models.CharField(max_length=20, null=False, blank=False)

    def __unicode__(self):
        return self.abbr


class Stock(models.Model):
    """
    Describes the type of Stock
    """
    type = models.CharField(max_length=10, choices=STOCK_TYPES, default='drug', null=False, blank=False,)
    abbr = models.CharField(max_length=10, null=True, blank=True)
    code = models.CharField(max_length=20, null=False, blank=False, unique=True)
    short_code = models.CharField(max_length=10, null=False, blank=True, unique=True)
    name = models.CharField(max_length=80, null=False, blank=False)
    units = models.ForeignKey(StockUnit, null=True, blank=True)

    def __unicode__(self):
        return "%s: %s" % (self.code, self.name)

    def save(self, * args, ** kwargs):
        self.short_code = "".join(filter(lambda x:x in string.letters + string.digits, list(self.code)))
        super(Stock, self).save(*args, ** kwargs)



class StockAccount(models.Model):
    """
    Contains the stock type, owning facility and amount of the stock. It also
    has helper properties and mesthods to get assigned threshold, supplied and
    expended amounts.
    """
    stock = models.ForeignKey(Stock, null=False, blank=False)
    location = models.ForeignKey(Location, limit_choices_to={"supportedlocation__supported": 'True'})
    amount = models.PositiveIntegerField(default=0, null=False, blank=False)
    pending_amount = models.PositiveIntegerField(default=0, null=False, blank=False)
    last_updated = models.DateTimeField(default=datetime.now, editable=False)
    stock_date = models.DateField(null=True, blank=True)

    def save(self, * args, ** kwargs):
        self.last_updated = datetime.now()
        if self.pk and not self.stock_date:
            self.stock_date = self.last_updated.date()
        super(StockAccount, self).save(*args, ** kwargs)
        Threshold.try_create_threshold(self)

    def __unicode__(self):
        return "%s > %s %s" % (self.stock, self.location, self.amount)

    @property
    def current_threshold(self):
        today = date.today()
        year = today.year
        month = today.month
        thresholds = Threshold.objects.filter(account__id=self.id).\
            filter(Q(end_date=None) | Q(end_date__year=year, end_date__month=month)).order_by('-id')
        if thresholds:
            return thresholds[0].level
        
    def threshold(self, today):
        year = today.year
        month = today.month
        thresholds = Threshold.objects.filter(account__id=self.id, start_date__year=year,
                                              start_date__month=month).\
            filter(Q(end_date=None) | Q(end_date__year=year, end_date__month=month)).order_by('-id')
        if thresholds:
            return thresholds[0].level

    def supplied(self, start_date, end_date):
        my_start_date = datetime(start_date.year, start_date.month, start_date.day)
        my_end_date = datetime(end_date.year, end_date.month, end_date.day)
        
        sum = 0
        supplies = StockTransaction.objects.filter(account_to=self,
                                                   transaction__date__gte=my_start_date).filter(transaction__date__lt=(my_end_date + timedelta(days=1)).date())

        for s in supplies:
            # @type s StockTransaction
            sum += s.amount

        return sum

    def expended(self, start_date, end_date):
        my_start_date = datetime(start_date.year, start_date.month, start_date.day)
        my_end_date = datetime(end_date.year, end_date.month, end_date.day)

        sum = 0
        
        expenses = StockTransaction.objects.filter(account_from=self,
                                                     transaction__date__gte=my_start_date).\
                                                     filter(
                                                     transaction__date__lt=(my_end_date +
                                                     timedelta(days=1)).date())


#        expenses = StockTransaction.objects.filter(transaction__in=out_transactions)

        for s in expenses:
            # @type s StockTransaction
            sum += s.amount

        return sum

    class Meta:
        unique_together = (('stock', 'location'),)


TRANSACTION_CHOICES = (
                       ('p', 'Pending'),
                       ('f', 'Failed'),
                       ('c', 'Completed'),
                       ('x', 'Cancelled'),
                       )

TRANSACTION_TYPES = (
                     ('d', 'Dispense'),
                     ('d_f', 'District to Facility'),
                     ('f_f', 'Facility to Facility'),
                     )


class Transaction(models.Model):
    """
    Keeps track of by who, when particular transactions took place
    """
    status = models.CharField(max_length=1, choices=TRANSACTION_CHOICES, default='p')
    web_user = models.ForeignKey(User, null=True, blank=True)
    sms_user = models.ForeignKey(Contact, null=True, blank=True)
    date = models.DateTimeField(default=datetime.now)
    reference = models.ForeignKey(ConfirmationCode, null=False, blank=False, unique=True)
    type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    valid = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s, %s, %s, %s" % (self.reference, self.status, self.type, self.date)

    def delete_transaction(self):
        stock_transactions = StockTransaction.objects.filter(transaction=self)
        affected = []
        for stock_trans in stock_transactions:
            account_from = stock_trans.account_from
            account_to = stock_trans.account_to
            if account_from:
                account_from.amount += stock_trans.amount
                account_from.save()
                affected.append(account_from)
            if account_to:
                account = StockAccount.objects.get(id=account_to.id)
                account.amount -= stock_trans.amount
                account.save()
                affected.append(account)
                # TODO: Consider better implementation than deleting
            stock_trans.delete()
            
        self.status = 'x'
        self.save()
        return affected


class Threshold(models.Model):
    account = models.ForeignKey(StockAccount, null=False, blank=False)
    level = models.PositiveIntegerField(blank=False, null=False)
    start_date = models.DateField(default=date.today, null=False, blank=False)
    end_date = models.DateField(null=True, blank=True, editable=False)

    @classmethod
    def try_create_threshold(cls, stock_account):
        today = date.today()
        if not Threshold.objects.filter(account=stock_account, start_date__lte=today).\
        filter(Q(end_date=None) | Q(end_date__gte=date.today())):
            Threshold.objects.create(account=stock_account, start_date=today, level=30)
        return False

    def save(self, * args, ** kwargs):
        super(Threshold, self).save(*args, ** kwargs)
        for t in Threshold.objects.filter(end_date=None, start_date__lte=self.start_date, account=self.account, id__lt=self.id).exclude(pk=self.pk):
            t.end_date = date.today()
            t.save()

    def __unicode__(self):
        return "Threshold of %s for %s starting %s to %s" % (self.level, self.account, self.start_date, self.end_date or "")


class StockTransaction(models.Model):
    """
    Belongs to a Transaction which can be done as a batch Transaction
    """
    amount = models.IntegerField(default=0, null=False, blank=False)
    transaction = models.ForeignKey(Transaction, null=False, blank=False)
    stock = models.ForeignKey(Stock, null=False, blank=False)
    account_from = models.ForeignKey(StockAccount, null=True, blank=True)
    account_to = models.ForeignKey(StockAccount, null=True, blank=True, related_name="account_transaction")

    def __unicode__(self):
        return "%s > %s: %s" % (self.stock, self.transaction, self.amount)

    class Meta:
        unique_together = (('stock', 'transaction'),)

#    def save(self, *args, **kwargs):
#        if not self.pk:
#            p_trans= self.transaction
#            if p_trans.type == 'd':
#                account_from = p_trans.account_from
#                account_from.amount -= abs(self.amount)
#                account_from.save()
#            if p_trans.type == 'f_f':
#                account_from = p_trans.account_from
#                account_from.amount -= abs(self.amount)
#                account_from.save()
#
#                account_to = p_trans.account_to
#                account_to.amount += abs(self.amount)
#                account_to.save()
#
#            if p_trans.type == 'd_f':
#                account_from = p_trans.account_from
#                account_from.amount -= abs(self.amount)
#                account_from.save()
#
#                account_to = p_trans.account_to
#                account_to.amount += abs(self.amount)
#                account_to.save()
#
#        super(StockAccount, self).save(*args, **kwargs)


class LowStockLevelNotification(models.Model):
    stock_account = models.ForeignKey(StockAccount)
    contact = models.ForeignKey(Contact,
    limit_choices_to=models.Q(is_active=True, location__type__slug__in=DISTRICT_SLUGS)
                                )
    date_logged = models.DateField(default=datetime.now, editable=False)
    week_of_year = models.PositiveSmallIntegerField(null=True, blank=True)
    level = models.PositiveSmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return "%s: %s - %s" % (self.date_logged.strftime('%d/%m/%Y %H:%M'),
                                self.contact, self.stock_account)

    def save(self, * args, ** kwargs):
        if not self.week_of_year and self.date_logged:
            self.week_of_year = self.date_logged.isocalendar()[1]

        super(LowStockLevelNotification, self).save(*args, ** kwargs)

    @classmethod
    def week(cls, date_value):
        return int(date_value.isocalendar()[1])

    def __unicode__(self):
        return "%s: %s - %s" % (self.week_of_year, self.stock_account, self.contact)

    class Meta:
        unique_together = (('stock_account', 'contact', 'week_of_year', 'level'), )


class Supported(models.Model):
    district = models.ForeignKey(Location, related_name='supported_districts',
                                limit_choices_to={'type__slug__in':DISTRICT_SLUGS})
    supported = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s: %s" % (self.district, "Supported" if self.supported else "Not Supported")

    class Meta:
        verbose_name_plural = "Supported"


class WMS(models.Model):
    stock = models.ForeignKey(Stock)
    active = models.BooleanField(default=True)
    ordering = models.SmallIntegerField(blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.stock.name, "Supported" if self.active else "Not Supported")


class WeeklyStockMonitoringReport(models.Model):
    """
    This model is used for  submitting items for the Weekly Stock Monitoring
    Tool. It does not take into account actual consumption at the facility but
    just get submissions for weekly 'Stock on hand' and 'Average monthly consumption'
    """
    week_start = models.DateField()
    week_end = models.DateField()
    location = models.ForeignKey(Location, limit_choices_to={"type__slug__in": list(CLINIC_SLUGS)})
    wms_stock = models.ForeignKey(WMS)
    soh = models.PositiveIntegerField(null=True, blank=True, verbose_name='Stock on hand')
    amc = models.PositiveIntegerField(null=True, blank=True, verbose_name='Average monthly consumption')
    mos = models.PositiveIntegerField(null=True, blank=True, verbose_name='Months of Supply', editable=False)
    expected_stockout_date = models.DateField(null=True, blank=True, editable=False)
    deprecated = models.BooleanField(default=False, editable=False)

    def save(self, * args, ** kwargs):
        if self.soh and self.amc:
            self.mos = self.soh // self.amc
            self.expected_stockout_date = self.week_end + timedelta(days = (30.4375 * self.soh) / self.amc)

        super(WeeklyStockMonitoringReport, self).save(*args, ** kwargs)

    def __unicode__(self):
        return "%s %s %s: %s" % (self.location, self.week_start, self.wms_stock.stock.name, self.soh)

    class Meta:
        unique_together = (('location', 'week_start', 'wms_stock',))
