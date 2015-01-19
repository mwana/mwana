from itertools import groupby
from operator import itemgetter

from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from django import forms

from datetime import date

from rapidsms.models import Contact
from rapidsms.router import send, lookup_connections

from django_tables2_reports.views import ReportTableView

from mwana import const

from mwana.apps.appointments.models import Appointment, Notification
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.labresults.models import EIDConfirmation, Result

from .filters import (PatientListFilter, ChildrenListFilter,
                      AppointmentFilter, PatientTraceFilter,
                      RemindersFilter, EIDConfirmationFilter,
                      ResultFilter, ContactsListFilter)
from .tables import (ChildrenListTable, MothersListTable,
                     AppointmentTable, PatientTraceTable,
                     RemindersTable, EIDConfirmationTable,
                     ResultTable, ContactsListTable)


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


def get_contact_choices():
    all_contacts = Contact.objects.all()
    contacts = []
    for c in all_contacts:
        if c.default_connection is not None:
            id = c.default_connection.identity
            contacts.append((id, id))
    return contacts


class ContactsForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)
    identities = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ContactsForm, self).__init__(*args, **kwargs)
        self.fields['message'].widget.attrs['placeholder'] = 'Message'

    def clean_identities(self):
        """Gets the connections for the selected contacts."""
        identities = self.cleaned_data.get('identities', '')
        identities = [x.strip() for x in identities.split(',') if x.startswith("+") and len(x) > 9]
        conn_airtel = []
        conn_tnm = []
        for network, numbers in groupby(sorted(identities), key=itemgetter(4)):
            if network == '9':
                conn_airtel = lookup_connections(backend="airtelsmpp",
                                                 identities=numbers)
            elif network == '8':
                conn_tnm = lookup_connections(backend="tnm",
                                              identities=numbers)
        return conn_airtel + conn_tnm

    def send(self):
        message = self.cleaned_data['message']
        connections = self.cleaned_data['identities']
        return send(message, connections)


@login_required
@require_POST
def send_message(request):
    try:
        form = ContactsForm(request.POST)
        if form.is_valid():
            message = form.send()
            if len(message.connections) == 1:
                return HttpResponse('Your message was sent to 1 recipient.')
            else:
                msg = 'Your message was sent to {0} ' \
                    'recipients.'.format(len(message.connections))
                return HttpResponse(msg)
        else:
            return HttpResponseBadRequest(unicode(form.errors))
    except:
        return


class ContactsList(FilteredSingleTableView):
    model = Contact
    table_class = ContactsListTable
    template_name = 'remindmi/contacts_list.html'
    filter_class = ContactsListFilter
    queryset = Contact.active.filter(Q(types=const.get_cba_type()))


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
