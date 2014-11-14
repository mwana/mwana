import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.help.models import HelpRequest


class HelpRequestTable(TableReport):
    # requisition_id = tables.Column(verbose_name='Patient ID')
    district = tables.Column(
        verbose_name='District',
        accessor='requested_by.contact.clinic.parent.name')

    def render_district(self, value, record):
        if record.requested_by.contact.clinic.parent.parent is not None:
            return record.requested_by.contact.clinic.parent.parent.name
        elif record.requested_by.contact.clinic.parent is not None:
            return record.requested_by.contact.clinic.parent.name
        else:
            return value

    class Meta:
        model = HelpRequest
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id',)
