# vim: ai ts=4 sts=4 et sw=4
"""

"""

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from mwana.apps.locations.models import Location
from mwana.apps.reminders.models import SentNotification
from rapidsms.contrib.messagelog.models import Message



class Command(LabelCommand):
    help = ("assign facilities ro reporing group\nUsage: tracing_analysis KEYWORD DISTRICT_NAMES"
    '\nE.g. tracing_analysis TOLD Monze Mazabuka')

    def handle(self, * args, ** options):
        pass


        if len(args) < 2:
            raise CommandError('Please specify Keyword followed by District Name(s).\n'
        'E.g. tracing_analysis TOLD Monze Mazabuka')

        keyword = args[0]
        print args[1:]
        district_names = args[1:]

        facilities = Location.objects.filter(parent__slug__endswith='00',
        parent__name__iregex='|'.join(name for name in district_names))

        print "_" * 60
        print "Processing %s for the following %s facilities: %s" % (keyword, len(facilities), ", ".join(fac.slug+": "+fac.name for fac in facilities))

        if keyword.lower() == 'told':
            self.notification_told_interval(facilities)
        elif keyword.lower() == 'told2':
            self.notification_told_interval_exact(facilities)


    def deidentify(self, name, deid=True):
        if not deid:
            return name
        return "***** ".join(n[:2] for n in name.split())

    def last_notified(self, cba_conn, toldtime):

        notification = SentNotification.objects.filter(date_logged__lt=toldtime,
                                               patient_event__cba_conn=cba_conn).\
                                               order_by('-date_logged')[0]
        return notification.date_logged, notification.patient_event.patient.name

    def last_notified(self, cba_conn, toldtime, who):

        notification = SentNotification.objects.filter(date_logged__lt=toldtime,
                                               patient_event__cba_conn=cba_conn,
                                               patient_event__patient__name__icontains=who).\
                                               order_by('-date_logged')[0]
        return notification.date_logged, notification.patient_event.patient.name


    def notification_told_interval(self, facilities):

        msgs = Message.objects.filter(direction='I',
                               contact__location__parent__in=facilities,
                               text__iregex='^told|^toll|^teld|^tod|^telld|^t0ld|^TOLD|^t01d|^t0ld').distinct()

        for msg in msgs:
            try:
                last_notified, remind_who = self.last_notified(msg.connection, msg.date)
                interval = msg.date - last_notified
                print "%s,%s,%s" %(interval, self.deidentify(remind_who, False), self.deidentify(msg.text[msg.text.index(' '):].strip(),False))
            except:
                pass

    def notification_told_interval_exact(self, facilities):

        msgs = Message.objects.filter(direction='I',
                               contact__location__parent__in=facilities,
                               text__iregex='^told|^toll|^teld|^tod|^telld|^t0ld|^TOLD|^t01d|^t0ld').distinct()

        for msg in msgs:
            try:
                told_who = msg.text[msg.text.index(' '):].strip()
                last_notified, remind_who = self.last_notified(msg.connection, msg.date, told_who)
                interval = msg.date - last_notified
                print "%s,%s,%s" %(interval, self.deidentify(remind_who, False), self.deidentify(told_who,False))
            except:
                pass

#    def told_confirm_interval(self, facilities):
#        keyword = "^cofirm|^confirm|^conferm|^confhrm|^cnfrm|^CONFIRM|^Confirm|^C0nfirm|^comfirm|^c0mfirm|^comferm|^comfhrm|^cmfrm|^CONFIRM|^C0NFIRM|^Comfirm|^C0mfirm|^confirmed|^confermed|^confhrmed|^cnfrmed|^CONFIRMed|^Confirmed|^comfirmed|^comfermed|^comfhrmed|^cmfrmed|^CONFIRMed|^Comfirmed"
#
#        msgs = Message.objects.filter(direction='I',
#                               contact__location__parent__in=facilities,
#                               text__iregex=keyword).distinct()
#
#        for msg in msgs:
#            try:
#                last_told, told_who = self.last_told(msg.connection, msg.date)
#                interval = msg.date - last_told
#                print "%s,%s,%s" %(interval, self.deidentify(told_who, False), self.deidentify(msg.text[msg.text.index(' '):].strip(),False))
#            except:
#                pass
        


    def __del__(self):
        pass
