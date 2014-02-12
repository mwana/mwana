# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import datetime
import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from mwana.apps.locations.models import Location
from datetime import timedelta
from rapidsms.models import Contact

class ConfirmationCode(models.Model):
    def __unicode__(self):
        return str(self.id).zfill(6)

STOCK_TYPES = (
               ('drug', 'Drugs'),
               ('test_kit', 'Test Kits'),
               )


class StockUnit(models.Model):
    abbr = models.CharField(max_length=10, null=True, blank=True)
    description = models.CharField(max_length=20, null=False, blank=False)

class Stock(models.Model):
    type = models.CharField(max_length=10, choices=STOCK_TYPES, default='drug', null=False, blank=False,)
    abbr = models.CharField(max_length=10, null=True, blank=True)
    code = models.CharField(max_length=10, null=False, blank=False, unique=True)
    short_code = models.CharField(max_length=10, null=False, blank=True, unique=True)
    name = models.CharField(max_length=80, null=False, blank=False)
    units = models.ForeignKey(StockUnit, null=True, blank=True)

    def __unicode__(self):
        return "%s: %s" % (self.code, self.name)

    def save(self, * args, ** kwargs):
        self.short_code = "".join(filter(lambda x:x in string.letters + string.digits, list(self.code)))
        super(Stock, self).save(*args, ** kwargs)


class StockAccount(models.Model):
    stock = models.ForeignKey(Stock, null=False, blank=False)
    location = models.ForeignKey(Location, limit_choices_to={"supportedlocation__supported": 'True'})
    amount = models.PositiveIntegerField(default=0, null=False, blank=False)
    pending_amount = models.PositiveIntegerField(default=0, null=False, blank=False)
    last_updated = models.DateTimeField(default=datetime.now, editable=False)

    def save(self, * args, ** kwargs):
        self.last_updated = datetime.now()
        super(StockAccount, self).save(*args, ** kwargs)
        Threshold.try_create_threshold(self)

    def __unicode__(self):
        return "%s > %s %s" % (self.stock, self.location, self.amount)

    @property
    def current_threshold(self):
        today = date.today()
        thresholds =  Threshold.objects.filter(account__id=self.id, start_date__lte=today).\
        filter(Q(end_date=None) | Q(end_date__gte=date.today())).order_by('-id')
        if thresholds:
            return thresholds[0]
        
    def threshold(self, today):
        thresholds =  Threshold.objects.filter(account__id=self.id, start_date__lte=today).\
        filter(Q(end_date=None) | Q(end_date__gte=date.today())).order_by('-id')
        if thresholds:
            return thresholds[0]

    def supplied(self, start_date, end_date):
        sum = 0
        supplies = StockTransaction.objects.filter(transaction__account_to=self,
        transaction__date__gte=start_date.date()).filter(transaction__date__lt=(end_date + timedelta(days=1)).date())

        for s in supplies:
            # @type s StockTransaction
            sum += s.amount

        return sum
        

    class Meta:
        unique_together = (('stock', 'location'), )


TRANSACTION_CHOICES = (
                       ('p', 'Pending'),
                       ('f', 'Failed'),
                       ('c', 'Completed'),
                       )

TRANSACTION_TYPES = (
                     ('d', 'Dispense'),
                     ('d_f', 'District to Facility'),
                     ('f_f', 'Facility to Facility'),
                     )

class Transaction(models.Model):
    status = models.CharField(max_length=1, choices=TRANSACTION_CHOICES, default='p')
    web_user = models.ForeignKey(User, null=True, blank=True)
    sms_user = models.ForeignKey(Contact, null=True, blank=True)
    account_from = models.ForeignKey(StockAccount, null=True, blank=True)
    account_to = models.ForeignKey(StockAccount, null=True, blank=True, related_name="account_transaction")
    date = models.DateTimeField(default=datetime.now)
    reference = models.ForeignKey(ConfirmationCode, null=False, blank=False)
    type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    valid = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s, %s, %s, %s" % (self.reference, self.status, self.type, self.date)


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
    amount = models.IntegerField(default=0, null=False, blank=False)
    transaction = models.ForeignKey(Transaction, null=False, blank=False)
    stock = models.ForeignKey(Stock, null=False, blank=False)

    def __unicode__(self):
        return "%s > %s %s" % (self.stock, self.transaction, self.amount)

    class Meta:
        unique_together = (('stock', 'transaction'), )

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
