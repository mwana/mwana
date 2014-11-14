# from __future__ import unicode_literals

# # from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.labresults.models import Result


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
