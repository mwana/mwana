# vim: ai ts=4 sts=4 et sw=4
"""
Reactivates deactivated users since a given date
"""
from rapidsms.models import Contact
from mwana.apps.userverification.models import UserVerification
from mwana.apps.userverification.models import DeactivatedUser
from django.core.management.base import LabelCommand
from django.core.management.base import CommandError

from datetime import datetime
import logging

logger = logging.getLogger(__name__)
class Command(LabelCommand):
    help = "Reactivates deactivated users since a given date"
    args = "<year month day>"
    label = 'year month day separated by spaces'

    def handle(self, * args, ** options):

        if len(args) != 3:
            raise CommandError('Please specify %s.' % self.label)
        year, month, day = args
        self.reactivate_users(datetime(int(year), int(month), int(day)))

    def reactivate_users(self, since):
        for da in DeactivatedUser.objects.filter(deactivation_date__gte=since).\
                exclude(contact__userverification__response__istartswith='no'):

            contact = da.contact
            if Contact.active.filter(name=contact.name,
                location=contact.location,
                connection__identity=da.connection.identity):
                print "Active contact %s (%s) already exists" % (contact.name, da.connection.identity)
                continue
            contact.is_active = True
            contact.save()
            conn = da.connection
            conn.contact = contact
            conn.save()
            UserVerification.objects.filter(request_date__gte=since, contact=contact).delete()
#        DeactivatedUser.objects.filter(deactivation_date__gte=since).\
#                exclude(contact__userverification__response__istartswith='no').delete()

    def __del__(self):
        pass
