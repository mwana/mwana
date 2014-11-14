from django.views.generic import DetailView
from django.db.models import Q

from datetime import date

from rapidsms.models import Contact

from django_tables2_reports.views import ReportTableView

from mwana import const

from mwana.apps.appointments.models import Appointment, Notification
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.labresults.models import EIDConfirmation, Result

from .filters import (PatientListFilter, ChildrenListFilter,
                      AppointmentFilter, PatientTraceFilter,
                      RemindersFilter, EIDConfirmationFilter,
                      ResultFilter)
from .tables import (ChildrenListTable, MothersListTable,
                     AppointmentTable, PatientTraceTable,
                     RemindersTable, EIDConfirmationTable,
                     ResultTable)


TODAY = date.today()


class MotherDetailView(DetailView):
    model = Contact
    template_name = 'remindmi/mother_detail.html'
    client_type = Q(types=const.get_patient_type())
    queryset = Contact.objects.filter(client_type)


class ChildDetailView(DetailView):
    model = Contact
    template_name = 'remindmi/child_detail.html'
    client_type = Q(types=const.get_patient_type())
    queryset = Contact.objects.filter(client_type)


class FilteredSingleTableView(ReportTableView):
    filter_class = None

    def get_table_data(self):
        self.filter = self.filter_class(
            self.request.GET,
            queryset=super(FilteredSingleTableView, self).get_table_data())
        return self.filter

    def get_context_data(self, **kwargs):
        context = super(FilteredSingleTableView, self).get_context_data(**kwargs)
        context['filter'] = self.filter
        return context


class MothersList(FilteredSingleTableView):
    model = Contact
    table_class = MothersListTable
    template_name = 'remindmi/mothers_list.html'
    filter_class = PatientListFilter
    queryset = Contact.objects.filter(Q(types=const.get_patient_type()))


class ChildrenList(FilteredSingleTableView):
    model = Contact
    table_class = ChildrenListTable
    template_name = 'remindmi/children_list.html'
    filter_class = ChildrenListFilter
    queryset = Contact.objects.filter(Q(types=const.get_child_type()))


class AppointmentList(FilteredSingleTableView):
    model = Appointment
    table_class = AppointmentTable
    template_name = 'remindmi/appointment_list.html'
    filter_class = AppointmentFilter
    queryset = Appointment.objects.filter(
        Q(date__lt=TODAY), status=1)


class PatientTraceList(FilteredSingleTableView):
    model = PatientTrace
    table_class = PatientTraceTable
    template_name = 'remindmi/traces_list.html'
    filter_class = PatientTraceFilter
    # queryset = PatientTrace.objects.filter()


class RemindersList(FilteredSingleTableView):
    model = Notification
    table_class = RemindersTable
    template_name = 'remindmi/reminders_list.html'
    filter_class = RemindersFilter
    queryset = Notification.objects.filter(Q(appointment__subscription__connection__contact__types=const.get_patient_type()))


class EIDConfirmationList(FilteredSingleTableView):
    model = EIDConfirmation
    table_class = EIDConfirmationTable
    template_name = 'remindmi/eid_list.html'
    filter_class = EIDConfirmationFilter
    queryset = EIDConfirmation.objects.filter(Q(result__result='P'))


class ResultList(FilteredSingleTableView):
    model = Result
    table_class = ResultTable
    template_name = 'remindmi/result_list.html'
    filter_class = ResultFilter
    queryset = Result.objects.filter(Q(verified='t'))
