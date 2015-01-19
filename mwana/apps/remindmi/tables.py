from __future__ import unicode_literals

from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_tables2_reports.tables import TableReport
from rapidsms.models import Contact
from mwana.apps.appointments.models import Appointment, Notification
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.labresults.models import EIDConfirmation
from mwana.apps.labresults.models import Result


class PatientReportTable(tables.Table):
    # Override lots of columns to create better column labels.
    # age = tables.Column(verbose_name='Age (Months)', orderable=False)
    # sex = tables.Column(orderable=False)
    # location = tables.Column(orderable=False)
    # reporter_id = tables.Column(verbose_name='Reporter')
    # patient_id = tables.Column(verbose_name='Patient')
    location = tables.Column(verbose_name='Facility')
    created_on = tables.Column(verbose_name='Registered On')
    district = tables.Column(verbose_name='District',
                             accessor='location.parent.name')

    def render_district(self, value, record):
        if record.location.parent.parent is not None:
            return record.location.parent.parent.name
        elif record.location.parent is not None:
            return record.location.parent.name
        else:
            return value

    def render_name(self, value, record):
        return mark_safe('''<a href=client/%s>%s</a>''' % (record.id, value))

    class Meta:
        model = Contact
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'modified_on', 'language', 'pin', 'alias',
                   'is_help_admin', 'last_updated', 'errors',
                   'interviewer_id', 'first_name', 'last_name',
                   'is_active', 'status')


class CSVPatientReportTable(PatientReportTable):
    district = tables.Column(verbose_name='District',
                             accessor='location.parent.name')

    def render_district(self, value, record):
        if record.location.parent.parent is not None:
            return record.location.parent.parent.name
        elif record.location.parent is not None:
            return record.location.parent.name
        else:
            return value

    def render_name(self, value):
        return value

    class Meta:
        model = Contact
        exclude = ('id', 'modified_on', 'language', 'pin', 'alias',
                   'is_help_admin', 'last_updated', 'errors',
                   'interviewer_id', 'first_name', 'last_name',
                   'is_active', 'status')


class PatientListTable(TableReport):
    location = tables.Column(verbose_name='Facility')
    created_on = tables.Column(verbose_name='Registered On')
    district = tables.Column(verbose_name='District',
                             accessor='location.parent.name')

    def render_district(self, value, record):
        if record.location.parent.parent is not None:
            return record.location.parent.parent.name
        elif record.location.parent is not None:
            return record.location.parent.name
        else:
            return value

    def render_name(self, value, record):
        return mark_safe('''<a href=%s>%s</a>''' % (record.id, value))

    class Meta:
        model = Contact
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'modified_on', 'language', 'pin', 'alias',
                   'is_help_admin', 'last_updated', 'errors',
                   'interviewer_id', 'first_name', 'last_name',
                   'is_active', 'status')


class CSVPatientListTable(PatientListTable):
    def render_name(self, value):
        return value


class ContactsListTable(PatientListTable):
    # contact = tables.Column(verbose_name='Mobile',
    #                         accessor='default_connection.identity')
    facility_id = tables.Column(verbose_name='HMIS Code',
                                accessor='location.slug')

    def render_name(self, value, record):
        return value

    def render_facility_id(self, value, record):
        if "zone" == record.location.type.slug:
            return record.location.parent.slug
        else:
            return record.location.slug

    class Meta:
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'modified_on', 'language', 'pin', 'alias',
                   'is_help_admin', 'last_updated', 'errors', 'date_of_birth',
                   'interviewer_id', 'first_name', 'last_name', 'volunteer',
                   'is_active', 'status', 'parent', 'created_on')
        sequence = ("name", "location", "district")


class MothersListTable(PatientListTable):
    class Meta:
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'modified_on', 'language', 'pin', 'alias',
                   'is_help_admin', 'last_updated', 'errors',
                   'interviewer_id', 'first_name', 'last_name',
                   'is_active', 'status', 'parent')


class ChildrenListTable(PatientListTable):
    def render_parent(self, value, record):
        return mark_safe(
            '''<a href=../mothers/%s>%s</a>''' % (record.id, value))

    class Meta:
        model = Contact
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'modified_on', 'language', 'pin', 'alias',
                   'is_help_admin', 'last_updated', 'errors',
                   'interviewer_id', 'first_name', 'last_name',
                   'is_active', 'status')


class AppointmentTable(TableReport):
    timeline = tables.Column(accessor=tables.utils.A('milestone.timeline'),
                             order_by="milestone.timeline")
    connection = tables.Column(
        accessor=tables.utils.A('subscription.connection'),
        order_by="subscription.connection")
    subscription = tables.Column(accessor=tables.utils.A('subscription.pin'),
                                 order_by="subscription.pin",
                                 verbose_name='Patient')
    milestone = tables.Column(orderable=False)

    class Meta:
        model = Appointment
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'notes')
        sequence = ("timeline", "...", "connection", "subscription")


class PatientTraceTable(TableReport):
    class Meta:
        model = PatientTrace
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'type', 'patient_event', 'messenger',
                   'confirmed_by', )


class RemindersTable(TableReport):
    class Meta:
        model = Notification
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'message', 'confirmed')


class EIDConfirmationTable(TableReport):
    class Meta:
        model = EIDConfirmation
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id',)


class ResultTable(TableReport):
    requisition_id = tables.Column(verbose_name='Patient ID')
    clinic_care_no = tables.Column(verbose_name='HCC Number')
    district = tables.Column(verbose_name='District',
                             accessor='clinic.parent.name')

    def render_district(self, value, record):
        if record.clinic.parent.parent is not None:
            return record.clinic.parent.parent.name
        elif record.clinic.parent is not None:
            return record.clinic.parent.name
        else:
            return value

    class Meta:
        model = Result
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('payload', 'requisition_id_search', 'clinic_code_unrec',
                   'result_detail', 'child_age_unit', 'mother_age',
                   'collecting_health_worker', 'coll_hw_title',
                   'record_change', 'old_value', 'verified')
