# vim: ai ts=4 sts=4 et sw=4

"""
Custom command that outputs data for facility managent.
"""
#TODO : Create a web report that outputs same fields as this management command

from django.core.management.base import LabelCommand
from mwana.const import get_province_type
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.training.models import Trained
from mwana.apps.training.models import TrainingSession
from mwana.apps.userverification.models import DeactivatedUser
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact


class Command(LabelCommand):
    help = ("\nUsage: facility_management hmis_code1"
            '\nE.g. facility_management 406012'
            '\nE.g. facility_management 4060 (to match all starting with 4060)')
    def build_contact_list(self, contacts):
        return "; ".join("%s:%s" % (c.name, c.default_connection.identity)
                         for c in contacts)
                                           
    def handle(self, * args, ** options):

        codes = args 
        delm = '|'
        field_labels = ['Province Name','District Name','Facility Name', 'Code', 'Registered Workers',
            'Users Removed By System', 'Date Of First SMS',
            'Date Of First DBS Results', 'Names Of Users Not Retrieving',
            'Dates Users Were Trained', 'Ever Had Printer', 'Printers In Use',
            'Are DBS Registers Used', 'DBS Samples', 'DBS Results']

        print delm.join(field_labels)
        facility_codes = []
        for code in codes:
            for loc in Location.objects.filter(slug__startswith=code, parent__parent__type=get_province_type()):
                facility_codes.append(loc.slug)
            
        for code in set(facility_codes):
            try:
                facility = Location.objects.get(slug=code)
            except Location.DoesNotExist:
                continue

            facility_name = facility.name
            registered_workers = self.build_contact_list(Contact.active.filter(
                                                         location=facility,
                                                         types__slug='worker')
                                                         )
            users_removed_by_system = "; ".join("%s:%s" % (du.contact.name,
                                                du.contact.default_connection.identity if du.contact.default_connection else "" )
                                                for du in DeactivatedUser.\
                                                objects.filter(
                                                contact__location=facility,
                                                contact__types__slug='worker'))


            date_of_first_sms = ""
            try:
                date_of_first_sms = Message.objects.filter(direction='I',
                                                           contact__location=facility).order_by('date')[0].date.strftime('%Y-%m-%d')
            except IndexError:
                pass
            try:
                date_of_first_dbs_results = Result.objects.filter(clinic=facility).\
                    exclude(result_sent_date=None).\
                    order_by('result_sent_date')[0].result_sent_date.strftime('%Y-%m-%d')
            except IndexError:
                date_of_first_dbs_results = ""

            retrieving = [msg.contact.id for msg in Message.objects.filter(text__icontains='here are y', contact__location=facility).exclude(text__icontains='9990;De')]
            names_of_users_not_retrieving = self.build_contact_list(Contact.active.filter(location=facility,
                                                                    types__slug='worker').exclude(id__in=retrieving))

            ts_dates = [ts.start_date.strftime('%Y-%m-%d')
            for ts in TrainingSession.objects.filter(location=facility)]
            trained_dates = [ts.date.strftime('%Y-%m-%d')
            for ts in Trained.objects.filter(location=facility)]
            demo_dates = [msg.date.strftime('%Y-%m-%d')
            for msg in Message.objects.filter(text__icontains='Demo',
                direction='I').filter(text__icontains=code)]
            dates_users_were_trained = "; ".join(set(ts_dates + trained_dates + demo_dates))
            ever_had_printer = "Yes" if Contact.objects.filter(location=facility, types__slug__icontains='printer').exists() else "No"
            printers_in_use = ""
            if ever_had_printer == "Yes": printers_in_use = str(Contact.active.filter(location=facility, types__slug='printer').count())

            are_dbs_registers_used = ""
            dbs_samples = str(Result.objects.filter(clinic=facility).count())
            dbs_results = str(Result.objects.filter(clinic=facility, notification_status='sent').count())
            district_name = facility.parent.name
            province_name = facility.parent.parent.name
            fields = [province_name, district_name, facility_name, code, registered_workers, users_removed_by_system
            , date_of_first_sms, date_of_first_dbs_results,
            names_of_users_not_retrieving, dates_users_were_trained,
            ever_had_printer, printers_in_use, are_dbs_registers_used,
            dbs_samples, dbs_results]
           
            print delm.join(fields)
        
    def __del__(self):
        pass
