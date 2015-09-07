# from __future__ import unicode_literals

# # from django.utils.safestring import mark_safe
import re
import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.labresults.models import Result, EIDConfirmation


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
                   'result_detail', 'child_age_unit', 'mother_age', 'id',
                   'collecting_health_worker', 'coll_hw_title', 'sample_id',
                   'record_change', 'old_value', 'verified')


class EIDConfirmationTable(TableReport):
    contact = tables.Column(accessor='contact.name')
    district = tables.Column(accessor='contact.clinic.parent.name')
    result_sent_date = tables.DateTimeColumn(accessor='result.result_sent_date')
    reported_on = tables.Column(verbose_name='Reported On')
    sample = tables.Column()
    # status = tables.Column()
    action_taken = tables.Column()
    art_number = tables.Column()
    hmis = tables.Column(accessor='contact.clinic.slug',
                         verbose_name='HMIS Code')

    def render_district(self, value, record):
        if record.contact.clinic.parent.parent is not None:
            return record.contact.clinic.parent.parent.name
        elif record.contact.clinic.parent is not None:
            return record.contact.clinic.parent.name
        else:
            return value

    def render_status(self, value, record):
        return value.upper()

    def render_action_taken(self, value, record):
        return value.upper()

    def clean_sample_hcc(self, id):
        id = re.sub('[- ]', '', line)
        return id

    # def render_result_sent_date(self, value, record):
    #     if value is None or value == '- - -':
    #         value = clean_sample_hcc(record.result.clinic_care_no)
          #     return value
          # else:
          #     value = clean_sample_hcc(record.result.requisition_id)
          #     return value

    class Meta:
        model = EIDConfirmation
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'result','status')
        sequence = ("contact", "hmis", "district", "reported_on", "sample",
                    "age_in_months", "action_taken", "art_number")

class EIDSummaryTable(TableReport):
    hmis = tables.Column(verbose_name='HMIS Code')
    district = tables.Column(verbose_name='District')
    result_count = tables.Column('Results Sent')
    sample_count = tables.Column('Results Delivered')
    art_count = tables.Column('ART Action Taken')
    cpt_count = tables.Column('CPT Action Taken')
    unknown_count = tables.Column('Unknown Action Taken')

    class Meta:
        attrs = {'class': "table table-striped table-bordered table-condensed",
                 'id': "facility-summary"}
        order_by = ('hmis',)

class EIDDistrictSummaryTable(TableReport):
    d_district = tables.Column(verbose_name='District')
    d_result_count = tables.Column('Results Sent')
    d_sample_count = tables.Column('Results Delivered')
    d_art_count = tables.Column('ART Action Taken')
    d_cpt_count = tables.Column('CPT Action Taken')
    d_unknown_count = tables.Column('Unknown Action Taken')

    class Meta:
        attrs = {'class': "table table-striped table-bordered table-condensed",
                 'id': "district-summary"}
        order_by = ('d_district',)
