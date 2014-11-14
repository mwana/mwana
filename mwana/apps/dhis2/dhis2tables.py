import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.dhis2.models import Submission


class SubmissionTable(TableReport):
    # requisition_id = tables.Column(verbose_name='Patient ID')
    district = tables.Column(
        verbose_name='District',
        accessor='location.parent.name')

    def render_district(self, value, record):
        if record.location.parent.parent is not None:
            return record.location.parent.parent.name
        elif record.location.parent is not None:
            return record.location.parent.name
        else:
            return value

    class Meta:
        model = Submission
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id',)
