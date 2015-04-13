# from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.monitor.models import MonitorSample

FACS_DISTRICTS = {
    '01': 'Chitipa',
    '02': 'Karonga',
    '03': 'Nkhata Bay',
    '04': 'Rumphi',
    '05': 'Mzimba',
    '06': 'Likoma',
    '10': 'Kasungu',
    '11': 'Nkhotakota',
    '12': 'Ntchisi',
    '13': 'Dowa',
    '14': 'Salima',
    '15': 'Lilongwe',
    '16': 'Mchinji',
    '17': 'Dedza',
    '18': 'Ntcheu',
    '25': 'Mangochi',
    '26': 'Machinga',
    '27': 'Zomba',
    '28': 'Chiradzulu',
    '29': 'Blantyre',
    '30': 'Mwanza',
    '31': 'Thyolo',
    '32': 'Mulanje',
    '33': 'Chikwawa',
    '34': 'Nsanje',
    '35': 'Phalombe',
    '36': 'Balaka',
    '37': 'Neno',
}


class MonitorSampleTable(TableReport):
    sample_id = tables.Column(verbose_name='Lab ID')
    lab_source = tables.Column(verbose_name='Laboratory',
                               accessor='payload.source')
    hmis = tables.Column(verbose_name='HMIS Code')
    district = tables.Column(verbose_name='District',
                             accessor='hmis')

    def render_district(self, value, record):
        if record.hmis is not None:
            return FACS_DISTRICTS[record.hmis[:2]]
        else:
            return value

    class Meta:
        model = MonitorSample
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'raw', 'sync')

class ResultsDeliveryTable(TableReport):
    name = tables.Column()
    hmis = tables.Column()
    district = tables.Column()
    all_new = tables.Column()
    all_notified = tables.Column()
    all_sent = tables.Column()
    new_today = tables.Column()
    sent_today = tables.Column()

    class Meta:
        attrs = {'class': "table table-striped table-bordered table-condensed"}


