from django.core.urlresolvers import reverse

from djtables import Table, Column
from djtables.column import DateColumn
from smsforms.models import XFormsSession
from .models import BirthRegistration, DeathRegistration, FacilityVisit, PregnantMother, ToldReminder
from utils import get_time_range


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
    scheduled_reminders = NamedColumn(sortable=False, col_name='Scheduled')
    sent_reminders = NamedColumn(sortable=False, col_name='Sent')
    received_told = NamedColumn(sortable=False, col_name='Received Told')
    follow_up_visit = NamedColumn(sortable=False, col_name='Follow Up visits')
    told_and_showed = NamedColumn(sortable=False, col_name='Told and showed')
    showed_on_time = NamedColumn(sortable=False, col_name='Showed on Time')


class SummaryReportTable(Table):
    data = Column(sortable=False)
    value = Column(sortable=False)

message_types = {
             'REG':'Pregnancy',
             'REFOUT':'Ref. Outcome',
             'RESP':'Ref. Response',
             'REFER':'Referral',
             'LOOK': 'Lookup',
             'FUP':'ANC',
             'JOIN':'User',
             'PP': 'PNC'
             }

def get_msg_type(message):
    if message.direction == "I":
        keyword = message.text.split(' ')[0]
        try:
            title = message_types[keyword.upper()]
        except KeyError:
            title = keyword
        finally:
            return title
    else:
        #This will need to be filled a little more to so that we can distinguish between valid and error messages.
        try:
            XFormsSession.objects.get(message_outgoing=message, has_error=True)
        except XFormsSession.DoesNotExist:
            return 'Response'
        else:
            return 'Error Response'

class CanNotGetKeywordMotherID(Exception):
    pass

def get_keyword_mother_id(message):
   
    if not message.text.strip():
        raise CanNotGetKeywordMotherID
    try:
        keyword = message.text.split(' ')[0]
        mother_id = message.text.split(' ')[1]
    except IndexError:
        raise CanNotGetKeywordMotherID
    return keyword.upper(), mother_id

def get_facility_visit(mother_id, limit_time):
    #Returns a facility visit given a motherid and some time to limit against
    time_range = get_time_range(limit_time, seconds=3600)
    try:
        facility_visit = FacilityVisit.objects.filter(mother__uid=mother_id, created_date__range=time_range)[0]
    except IndexError:
        return None
    else:
        return facility_visit

def get_pregnant_mother(mother_id, limit_time):
    time_range = get_time_range(limit_time, seconds=3600)
    try:
        pregnant_mother = PregnantMother.objects.filter(uid=mother_id, created_date__range=time_range)[0]
    except IndexError:
        return None
    else:
        return pregnant_mother

def get_death_registration(mother_id):
    try:
        death_registration = DeathRegistration.objects.filter(unique_id=mother_id)[0]
    except IndexError:
        return None
    else:
        return death_registration

def get_told_reminders(mother_id):
    try:
        told_reminder = ToldReminder.objects.filter(mother__uid=mother_id)[0]
    except IndexError:
        return None
    else:
        return told_reminder

def get_birth_registrations(mother_id):
    try:
        birth = BirthRegistration.objects.filter(mother__uid=mother_id)[0]
    except IndexError:
        return None
    else:
        return birth

def map_message_fields(message):
    #Returns an incoming message text with the various fields mapped to value. Some of the keywords have database objects that easily map to
    #session id and we can easily find the associated object, others require a little more work. 
    text = message.text
    if message.direction == "I":#only process the incoming messages, outgoing messages will continue just using the message text.
        database_obj = None
        try:
            keyword, mother_id = get_keyword_mother_id(message)
        except CanNotGetKeywordMotherID:
            return text
        if keyword == 'FUP' or keyword == 'PP':
            database_obj = get_facility_visit(mother_id, message.date)
        elif keyword == 'REG':
            database_obj = get_pregnant_mother(mother_id, message.date)
        elif keyword == 'DEATH':
            database_obj = get_death_registration(mother_id)
        elif keyword == 'TOLD':
            database_obj = get_told_reminders(mother_id) 
        elif keyword == "BIRTH":
            database_obj = get_birth_registrations(mother_id)
                
        if database_obj:
            text = database_obj.get_field_value_mapping()
    
    return text
    
class SMSRecordsTable(Table):
    date = DateColumn(format="Y m d H:i")
    phone_number = NamedColumn(col_name="Phone Number", value= lambda cell: cell.object.connection.identity)
    user_name = NamedColumn(link=lambda cell: reverse("sms-user-history", args=[cell.object.connection.contact.id]), col_name="User Name", value= lambda cell: cell.object.connection.contact.name.title())
    msg_type = NamedColumn(col_name="Type",
                      value=lambda cell: get_msg_type(cell.object),
                      sortable=False
                    )
    facility = Column(value=lambda cell: cell.object.connection.contact.location if cell.object.connection.contact else '')
    text = NamedColumn(col_name="Message", value=lambda cell:map_message_fields(cell.object))

    class Meta:
        order_by = "-date"

class ANCDeliveryTable(Table):
    pregnant = NamedColumn(col_name='Pregnant Women')
    two_anc = NamedColumn(col_name='2 ANC')
    three_anc = NamedColumn(col_name='3 ANC')
    four_anc = NamedColumn(col_name='4+ ANC')
    facility = NamedColumn(col_name='Facility')
    home = NamedColumn(col_name='Unknown')
    gestational_age = NamedColumn(col_name='Gestational Age @ First ANC')
    
class PNCReport(Table):
    registered_deliveries = NamedColumn(col_name='Registered Deliveries')
    facility = NamedColumn(col_name='Facility')
    community = NamedColumn(col_name='Community')
    six_hour_pnc = NamedColumn(col_name='6 Hour PNC')
    six_day_pnc = NamedColumn(col_name='6 Day PNC')
    six_week_pnc = NamedColumn(col_name='6 Week PNC')
    complete_pnc = NamedColumn(col_name='Complete PNC')
    mmr = NamedColumn(col_name='MMR')
    nmr = NamedColumn(col_name='NMR')
    
class ReferralReport(Table):
    emergent_referrals = NamedColumn(col_name='Emergent Referrals')
    emergent_responses = NamedColumn(col_name='Referrals w/ Response')
    emergent_response_outcome = NamedColumn(col_name='Referrals w/ response outcome')
    transport_with_ambulance = NamedColumn(col_name='Transport by Ambulance')
    average_turnaround_time = NamedColumn(col_name='Average Turnaround Time')
    common_complication = NamedColumn(col_name='Common Obstetric Complication')

class UserReport(Table):
    clinic_workers_registered = NamedColumn(col_name='Clinic Workers Registered')
    clinic_workers_active = NamedColumn(col_name='Clinic Workers Active')
    data_clerks_registered = NamedColumn(col_name='Data Clerks Registered')
    data_clerks_active = NamedColumn(col_name='Data Clerks Active')
    cbas_registered = NamedColumn(col_name='CBAs Registered')
    cbas_active = NamedColumn(col_name='CBAs Active')
    error_rate_clinic_workers = NamedColumn(col_name='Error Rate: Clinic Workers')
    error_rate_clinic_workers = NamedColumn(col_name='Error Rate: Data Clerks')
    error_rate_cbas = NamedColumn(col_name='Error Rate: CBAS')
    
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
