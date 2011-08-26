# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.db.models import Q
from mwana.apps.locations.models import Location
from mwana.util import get_clinic_or_default
from rapidsms.contrib.messagelog.models import Message

class MessageFilter:
    def __init__(self, current_user=None, group=None, province=None, district=None, facility=None):
        self.user = current_user
        self.reporting_group = group
        self.reporting_province = province
        self.reporting_district = district
        self.reporting_facility = facility

    
    today = date.today()
    dbsr_enddate = datetime(today.year, today.month, today.day) + \
        timedelta(days=1) - timedelta(seconds=0.01)
    dbsr_startdate = datetime(today.year, today.month, today.day) - \
        timedelta(days=30)

    def safe_rounding(self, float):
        try:
            return int(round(float))
        except TypeError:
            return None

    def set_reporting_period(self, startdate, enddate):
        if startdate:
            self.dbsr_startdate = datetime(startdate.year, startdate.month,
                                           startdate.day)
        if enddate:
            self.dbsr_enddate = \
            datetime(enddate.year, enddate.month, enddate.day)\
            + timedelta(days=1) - timedelta(seconds=0.01)

    def user_facilities(self):
        from mwana.locale_settings import SYSTEM_LOCALE, LOCALE_MALAWI, LOCALE_ZAMBIA
        if SYSTEM_LOCALE == LOCALE_ZAMBIA:
            facs = Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=self.user)
            if self.reporting_group:
                facs = facs.filter(Q(groupfacilitymapping__group__id=self.reporting_group) | Q(groupfacilitymapping__group__name__iexact=self.reporting_group))


            if self.reporting_facility:
                facs = facs.filter(slug=self.reporting_facility)
            elif self.reporting_district:
                facs = facs.filter(slug__startswith=self.reporting_district[:4])
            elif self.reporting_province:
                facs = facs.filter(slug__startswith=self.reporting_province[:2])
            return facs
        else:
            return Location.objects.all()

    def get_rpt_provinces(self, user):
        self.user = user
        return self.get_distinct_parents(self.get_rpt_districts(user))

    def get_distinct_parents(self, locations):
        if not locations:
            return []
        parents = []
        for location in locations:
            parents.append(location.parent)
        return list(set(parents))

    def get_rpt_districts(self, user):
        self.user = user
        return self.get_distinct_parents(Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=self.user))

    def get_rpt_facilities(self, user):
        self.user = user
        return Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=self.user)


    def get_active_facilities(self):
        return self.user_facilities().filter(lab_results__notification_status__in=
                                             ['sent']).distinct()

   

    def get_facilities_for_reporting(self):
        facs = Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=self.user)
        if self.reporting_group:
            facs = facs.filter(Q(groupfacilitymapping__group__id=self.reporting_group)
                               | Q(groupfacilitymapping__group__name__iexact=self.reporting_group))
        if self.reporting_facility:
                facs = facs.filter(slug=self.reporting_facility)
        elif self.reporting_district:
            facs = facs.filter(slug__startswith=self.reporting_district[:4])
        elif self.reporting_province:
            facs = facs.filter(slug__startswith=self.reporting_province[:2])
        return facs.filter(supportedlocation__supported=True
                           ).distinct()

    def get_filtered_message(self, text):
        text_copy = text
        key_texts = ["Patient ID:", "***", ". IDs :"]
        for key_text in key_texts:
            if key_text in text:
                text_copy = text[:text.index(key_text)+len(key_text)] + "*** " * text.count(key_text)
                break
        return text_copy

    def get_filtered_message_logs(self, startdate=None, enddate=None, search_key=None):
        self.set_reporting_period(startdate, enddate)

        locations = Q(contact__location__in=self.get_facilities_for_reporting()) |\
                               Q(contact__location__parent__in=self.get_facilities_for_reporting())
        daterange = Q(date__gte=self.dbsr_startdate) & Q(date__lte=self.dbsr_enddate)

        msgs = Message.objects.filter(locations).filter(daterange).order_by('-date')[:200]

        

        if search_key and search_key.strip():
            search = Q(text__icontains=search_key) |\
            Q(connection__identity__icontains=search_key.strip()) |\
            Q(contact__name__icontains=search_key.strip())
            msgs = Message.objects.filter(locations).filter(daterange).filter(search).order_by('-date')[:200]

        table = []

        table.append(['  Date', '  Clinic', 'Direction', 'Who', 'Phone number',
                     'Text'])

        for msg in msgs:
            date = str(msg.date)[:-4]
            clinic = get_clinic_or_default(msg.contact)
            direction = msg.direction
            name = msg.contact.name if msg.contact else None
            phone = msg.connection.identity
            text = msg.text
            text =self.get_filtered_message(text)
            table.append([date,clinic, direction,\
                      name, phone, text])
        return table
#        return sorted(table, key=itemgetter(0, 1))
