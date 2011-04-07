# vim: ai ts=4 sts=4 et sw=4
"""
In Reminders.patient_event some CBA connectins were created using wrong backend
because modem ports were accidentally swapped and owing to the implementation of
registering births which does not require one to be a registered CBA.
Idealy 097.. numbers and 096.. should use separate backends. the 096 backend does
not support outgoing 097 connections

"""

from datetime import date

from django.core.management.base import LabelCommand
from mwana.apps.reminders.models import PatientEvent
from rapidsms.models import Connection



class Command(LabelCommand):
    help = "Tries to assign CBA connection to the right CBAs."
    
    def handle(self, * args, ** options):
        start_date = date(2011, 3, 1)
        identity_start = '+26097'
        wrong_backend_name = 'mtn'
        right_backend_name = 'zain'
        self.assign_right_backend(start_date, identity_start, wrong_backend_name, right_backend_name)

        identity_start = '+26096'
        wrong_backend_name = 'zain'
        right_backend_name = 'mtn'
        self.assign_right_backend(start_date, identity_start, wrong_backend_name, right_backend_name)
        
    def assign_right_backend(self,start_date,identity_start,wrong_backend_name,right_backend_name):
        patient_events = PatientEvent.objects.filter(date__gte=start_date,cba_conn__identity__startswith=identity_start, cba_conn__backend__name=wrong_backend_name)
        for pe in patient_events:
            try:
                correct_connection = Connection.objects.get(identity=pe.cba_conn.identity,backend__name=right_backend_name)
                pe.cba_conn = correct_connection
                pe.save()
                contact = correct_connection.contact.name if correct_connection else "None"
                print "connection with '%s' changed to '%s' for %s for %s logged on %s" % (wrong_backend_name,right_backend_name,pe.cba_conn.identity, contact, pe.date)
            except Exception, e:
                print "Oops! caught exeption:\n", e.message

    def __del__(self):
        pass
