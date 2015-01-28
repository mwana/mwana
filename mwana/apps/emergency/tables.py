import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.emergency.models import FloodReport


class FloodReportTable(TableReport):
    district = tables.Column(
        verbose_name='District',
        accessor='reported_by.contact.clinic.parent.name')
    facility = tables.Column(
        verbose_name='Facility',
        accessor='reported_by.contact.clinic.name')
    facility_id = tables.Column(
        verbose_name='HMIS Code',
        accessor='reported_by.contact.location')
    reported_by = tables.Column(
        verbose_name='Reported By',
        accessor='reported_by.contact.name')

    def render_district(self, value, record):
        if record.reported_by.contact.clinic.parent.parent is not None:
            return record.reported_by.contact.clinic.parent.parent.name
        elif record.reported_by.contact.clinic.parent is not None:
            return record.reported_by.contact.clinic.parent.name
        else:
            return value

    def render_facility_id(self, value, record):
        if "zone" == record.reported_by.contact.location.type.slug:
            return record.reported_by.contact.location.parent.slug
        else:
            return record.reported_by.contact.location.slug

    class Meta:
        model = FloodReport
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'status', 'comments', 'addressed_on', 'resolved_by',
                   'notes',)
        order_by = ('-reported_on',)
