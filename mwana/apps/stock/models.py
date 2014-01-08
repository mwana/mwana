# vim: ai ts=4 sts=4 et sw=4
from django.contrib.auth.models import User
from rapidsms.models import Contact
from mwana.apps.locations.models import Location
from django.db import models
from datetime import datetime, date

class ConfirmationCode(models.Model):
    def __unicode__(self):
        return str(self.id).zfill(6)

STOCK_TYPES = (
    ('drug', 'Drugs'),
    # ('drug','Drugs'),
)


class StockUnit(models.Model):
    abbr = models.CharField(max_length=10, null=True, blank=True)
    description = models.CharField(max_length=20, null=False, blank=False)

class Stock(models.Model):
    type = models.CharField(max_length=10, choices=STOCK_TYPES, null=False, blank=False)
    abbr = models.CharField(max_length=10, null=True, blank=True)
    code = models.CharField(max_length=10, null=False, blank=False, unique=True)
    name = models.CharField(max_length=30, null=False, blank=False)
    units = models.ForeignKey(StockUnit, null=True, blank=True)

    def __unicode__(self):
        return "%s: %s" % (self.code, self.name)



class StockAccount(models.Model):
    stock = models.ForeignKey(Stock, null=False, blank=False)
    location = models.ForeignKey(Location, limit_choices_to={"type__slug__iregex": "[^zone]"})
    amount = models.PositiveIntegerField(default=0, null=False, blank=False)
    pending_amount = models.PositiveIntegerField(default=0, null=False, blank=False)
    last_updated = models.DateTimeField(default=datetime.now, editable=False)

    def save(self, *args, **kwargs):
        self.last_updated = datetime.now()
        super(StockAccount, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s > %s %s" % (self.stock, self.location, self.amount)

    class Meta:
        unique_together = (('stock', 'location'),)


TRANSACTION_CHOICES = (
    ('p', 'Pending'),
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

#
#    def __unicode__(self):
#        return "%s, %s, %s, %s" % (self.reference, self.status, self.type, self.date)

class Threshold(models.Model):
    account = models.ForeignKey(StockAccount, null=False, blank=False)
    level = models.PositiveIntegerField(blank=False, null=False)
    start_date = models.DateField(default=date.today, null=False, blank=False)
    end_date = models.DateField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        super(Threshold, self).save(*args, **kwargs)
        for t in Threshold.objects.filter(end_date=None, start_date__lte=self.start_date, account=self.account).exclude(pk=self.pk):
            t.end_date = date.today()
            t.save()
class StockTransaction(models.Model):
    amount = models.IntegerField(default=0, null=False, blank=False)
    transaction = models.ForeignKey(Transaction, null=False, blank=False)
    stock = models.ForeignKey(Stock, null=False, blank=False)

    def __unicode__(self):
        return "%s > %s %s" % (self.stock, self.transaction, self.amount)

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





