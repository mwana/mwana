from django.core.urlresolvers import reverse

from djtables import Table, Column
from djtables.column import DateColumn


class NamedColumn(Column):
    """
    A custom Column class that allows for a non-field based Column Name
    """
    def __init__(self, col_name=None, *args, **kwargs):
        super(NamedColumn, self).__init__(*args, **kwargs)
        self._col_name = col_name
        self._header_class = "upper"

    def __unicode__(self):
        return self._col_name or self.name


class PregnantMotherTable(Table):
    created_date = DateColumn(format="Y m d H:i ")
    uid = Column(link=lambda cell: reverse("mother-history", args=[cell.object.id]))
    location = Column()
    edd = DateColumn(format="d/m/Y")
    risks = Column(value=lambda cell: ", ".join([x.upper() \
                                     for x in cell.object.get_risk_reasons()]),
                   sortable=False)

    class Meta:
        order_by = "-created_date"


class MotherMessageTable(Table):
    date = DateColumn(format="Y m d H:i ")
    msg_type = NamedColumn(col_name="Type",
                      value=lambda cell: cell.object.text.split(' ')[0].upper(),
                      sortable=False)
    contact = NamedColumn(col_name="Sender")
    facility = Column(value=lambda cell: cell.object.contact.location.name if cell.object.contact else '')
    text = NamedColumn(col_name="Message")

    class Meta:
        order_by = "-date"


class NotificationsTable(Table):
    date = DateColumn(format="Y m d H:i ")
    facility = Column(value=lambda cell: cell.object.contact.location.name if cell.object.contact else '')
    text = NamedColumn(col_name="Message")

    class Meta:
        order_by = "-date"


class ReferralsTable(Table):
    date = DateColumn(format="Y m d H:i ")
    from_facility = Column()
    sender = Column(value=lambda cell: cell.object.session.connection.contact if cell.object.session.connection else '', sortable=False)
    number = Column(value=lambda cell: cell.object.session.connection.identity if cell.object.session.connection else '', sortable=False)
    response = Column(value=lambda cell: "Yes" if cell.object.responded else "No", sortable=False)
    status = Column()
    confirm_amb = Column(value=lambda cell: cell.object.ambulance_response, sortable=False)
    outcome = Column(sortable=False)
    message = Column(value=lambda cell: cell.object.session.message_incoming.text if cell.object.session.message_incoming else '',
                     sortable=False)
    flag = Column(value=lambda cell: '<div class="status {0}">&nbsp;</div>'.format(cell.object.flag), sortable=False, safe=True)

    class Meta:
        order_by = "-date"


class StatisticsTable(Table):
    location = Column(header_class="location")
    pregnancies = Column()
    births_com = NamedColumn(col_name="COM")
    births_fac = NamedColumn(col_name="FAC")
    births_total = NamedColumn(col_name="Total")
    infant_deaths_com = NamedColumn(col_name="COM")
    infant_deaths_fac = NamedColumn(col_name="FAC")
    infant_deaths_total = NamedColumn(col_name="Total")
    mother_deaths_com = NamedColumn(col_name="COM")
    mother_deaths_fac = NamedColumn(col_name="FAC")
    mother_deaths_total = NamedColumn(col_name="Total")
    anc1 = NamedColumn(col_name="1 ANC")
    anc2 = NamedColumn(col_name="2 ANCs")
    anc3 = NamedColumn(col_name="3 ANCs")
    anc4 = NamedColumn(col_name="4 ANCs")
    pos1 = NamedColumn(col_name="1 POS")
    pos2 = NamedColumn(col_name="2 POS")
    pos3 = NamedColumn(col_name="3 POS")


class StatisticsLinkTable(StatisticsTable):

    location = Column(link=lambda cell:
                                reverse("district-stats",
                                    args=[cell.object['location_id']]
                                ),
                      header_class="location"
                    )
    pregnancies = Column()
    births_com = NamedColumn(col_name="COM")
    births_fac = NamedColumn(col_name="FAC")
    births_total = NamedColumn(col_name="Total")
    infant_deaths_com = NamedColumn(col_name="COM")
    infant_deaths_fac = NamedColumn(col_name="FAC")
    infant_deaths_total = NamedColumn(col_name="Total")
    mother_deaths_com = NamedColumn(col_name="COM")
    mother_deaths_fac = NamedColumn(col_name="FAC")
    mother_deaths_total = NamedColumn(col_name="Total")
    anc1 = NamedColumn(col_name="1 ANC")
    anc2 = NamedColumn(col_name="2 ANCs")
    anc3 = NamedColumn(col_name="3 ANCs")
    anc4 = NamedColumn(col_name="4 ANCs")
    pos1 = NamedColumn(col_name="1 POS")
    pos2 = NamedColumn(col_name="2 POS")
    pos3 = NamedColumn(col_name="3 POS")


class ReminderStatsTable(Table):
    reminder_type = NamedColumn(sortable=False, header_class="reminder-type", col_name="Number Of Mothers With:")
    reminders = NamedColumn(sortable=False, col_name="Reminders")
    showed_up = NamedColumn(sortable=False, col_name="Showed Up")
    told = NamedColumn(sortable=False, col_name="Told")
    told_and_showed = NamedColumn(sortable=False, col_name="Showed Up Due to Told")


class SummaryReportTable(Table):
    data = Column(sortable=False)
    value = Column(sortable=False)

message_types = {
             'REG':'Pregnancy',
             'REFOUT':'Ref. Outcome',
             'RESP':'Ref. Response',
             'REFER':'Referral',
             'REG':'Pregnancy',
             'LOOK': 'Lookup',
             'FUP':'ANC',
             'JOIN':'User'
             }
def get_msg_type(message_type):
    try:
        title = message_types[message_type.upper()]
    except KeyError:
        title = message_type
    finally:
        return title
    
class SMSRecordsTable(Table):
    date = DateColumn(format="Y m d H:i")
    phone_number = NamedColumn(col_name="Phone Number", value= lambda cell: cell.object.connection.identity)
    user_name = NamedColumn(link=lambda cell: reverse("sms-user-history", args=[cell.object.connection.contact.id]), col_name="User Name", value= lambda cell: cell.object.connection.contact.name.title())
    msg_type = NamedColumn(col_name="Type",
                      #value=lambda cell: cell.object.text.split(' ')[0].upper(),
                      value=lambda cell: get_msg_type(cell.object.text.split(' ')[0]),
                      sortable=False
                    )
    facility = Column(value=lambda cell: cell.object.connection.contact.location if cell.object.connection.contact else '')
    text = NamedColumn(col_name="Message")

    class Meta:
        order_by = "-date"


class SMSUsersTable(Table):
    created_date = DateColumn(format="Y m d ")
    name = Column(link=lambda cell: reverse("sms-user-history", args=[cell.object.id]))
    number = Column(value=lambda cell: cell.object.default_connection.identity if cell.object.default_connection else '',
                    sortable=False)
    last_active = DateColumn(value=lambda cell: cell.object.latest_sms_date,
                         format="Y m d H:i",
                         sortable=False)
    location = Column(value=lambda cell: cell.object.location.name if cell.object.location else '',)
    active_status = Column(value=lambda cell: '<div class="status {0}">&nbsp;</div>'.format(cell.object.active_status), sortable=False, safe=True)

    class Meta:
        order_by = "-created_date"


class SMSUserMessageTable(Table):
    date = DateColumn(format="Y m d H:i")
    msg_type = NamedColumn(col_name="Type",
                      value=lambda cell: cell.object.text.split(' ')[0].upper(),
                      sortable=False
                    )
    text = NamedColumn(col_name="Message")

    class Meta:
        order_by = "-date"


class HelpRequestTable(Table):
    id = Column(link=lambda cell: reverse("help-manager", args=[cell.object.id]))
    requested_on = DateColumn(format="Y m d H:i ")
    phone = Column(value=lambda cell: cell.object.requested_by.identity)
    name = Column(value=lambda cell: cell.object.requested_by.contact.name if cell.object.requested_by.contact else '')
#    title = Column(value=lambda cell: ", ".join([x for x in cell.object.requested_by.contact.types.all()]) if cell.object.requested_by.contact else '',
#                   sortable=False)
    facility = Column(value=lambda cell: cell.object.requested_by.contact.location if cell.object.requested_by.contact else '')
    additional_text = NamedColumn(col_name='message')
    resolved_by = Column(value=lambda cell: cell.object.resolved_by or 'Unresolved')
    status = Column(value=lambda cell: '<div class="status {0}">&nbsp;</div>'.format(cell.object.get_status_display), sortable=False, safe=True)

    class Meta:
        order_by = "-requested_on"
