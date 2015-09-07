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
    patientid = tables.Column(verbose_name='Sample ID',
                              accessor='result.requisition_id')
    hcc = tables.Column(verbose_name='HCC ID',
                        accessor='result.clinic_care_no')
    sample_id = tables.Column(verbose_name='Lab Sample ID')
    lab_source = tables.Column(verbose_name='Laboratory',
                               accessor='payload.source')
    hmis = tables.Column(verbose_name='HMIS Code')
    facility = tables.Column(verbose_name='Facility',
                             accessor='result.clinic.name')
    district = tables.Column(verbose_name='District',
                             accessor='hmis')
    entered = tables.Column(verbose_name='Processed in LIMS',
                            accessor='result.processed_on')
    arrival = tables.Column(verbose_name='Entry in RapidSMS',
                            accessor='result.arrival_date')
    sent = tables.Column(verbose_name='Result Sent Date',
                         accessor='result.result_sent_date')
    recipient = tables.Column(verbose_name='Recipient',
                              accessor='result.recipient.contact')
    recipient_type = tables.Column(verbose_name="Recipient Type",
                                   accessor='result.recipient.contact')
    # confirmation = tables.Column(verbose_name='Receipt Confirmation',
    # accessor='??)

    def render_district(self, value, record):
        if record.hmis is not None:
            if record.hmis[:2] not in FACS_DISTRICTS.keys():  # faulty data
                return "Unknown District"
            else:
                return FACS_DISTRICTS[record.hmis[:2]]
        else:
            return "Unknown"

    def render_patient_id(self, value, record):
        if len(record.result.requisition_id) < 7:
            return record.result.clinic_care_no
        else:
            return record.result.requisition_id

    def render_recipient_type(self, value, record):
        if record is not None:
            if record.result.recipient.contact is not None:
                return ', '.join(
                    record.result.recipient.contact.types.values_list(
                        'name', flat=True))
        else:
            return value

    class Meta:
        model = MonitorSample
        attrs = {'class': "table table-striped table-bordered table-condensed"}
        exclude = ('id', 'raw', 'sync', 'result')
        sequence = ("sample_id", "lab_source", "patientid", "hcc", "facility",
                    "hmis", "district", "entered", "status", "arrival", "sent",
                    "recipient", "recipient_type", "payload")
        order_by = ('-entered')


class ResultsDeliveryTable(TableReport):
    name = tables.Column()
    hmis = tables.Column()
    district = tables.Column()
    all_new = tables.Column(verbose_name="Pending Retrieval")
    # all_notified = tables.Column()
    # all_sent = tables.Column()
    # new_today = tables.Column()
    # sent_today = tables.Column()
    num_lims = tables.Column(verbose_name="Total in LIMS")
    num_rsms = tables.Column(verbose_name="Total in RapidSMS")
    num_sent_out = tables.Column(verbose_name="Total Sent Out")
    sent_printer = tables.Column(verbose_name="Sent to Printer")
    sent_worker = tables.Column(verbose_name="Sent to Phone")
    percentage_sent = tables.Column(verbose_name="Percentage Sent by RapidSMS")
    # receipt_confirmed = tables.Column(verbose_name="Confirmed by Recipient")

    class Meta:
        attrs = {'class': "table table-striped table-bordered table-condensed"}