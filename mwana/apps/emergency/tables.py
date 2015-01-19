import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.emergency.models import FloodReport


class FloodReportTable(TableReport):
    district = tables.Column(
        verbose_name='District',
        accessor='reported_by.contact.clinic.parent.name')

    def render_district(self, value, record):
        if record.reported_by.contact.clinic.parent.parent is not None:
            return record.reported_by.contact.clinic.parent.parent.name
        elif record.reported_by.contact.clinic.parent is not None:
            return record.reported_by.contact.clinic.parent.name
        else:
            return value

    class Meta:
        model = FloodReport
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id',)
