# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.db.models import Q
from mwana.apps.locations.models import Location
from mwana.util import get_clinic_or_default
from rapidsms.contrib.messagelog.models import Message
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class MessageFilter:
    def __init__(self, current_user=None, group=None, province=None, district=None, facility=None, worker_types=[]):
        self.user = current_user
        self.reporting_group = group
        self.reporting_province = province
        self.reporting_district = district
        self.reporting_facility = facility
        self.worker_types = worker_types

    
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

    def get_filtered_message_logs(self, startdate=None, enddate=None, search_key=None, page=1):
        """
        Returns censored message logs (with Requisition IDs, Results hidden)
        """
        self.set_reporting_period(startdate, enddate)

        locations = Q(contact__location__in=self.get_facilities_for_reporting()) |\
                               Q(contact__location__location__in=self.get_facilities_for_reporting())|\
                               Q(contact__location__location__location__in=self.get_facilities_for_reporting())|\
                               Q(contact__location__parent__in=self.get_facilities_for_reporting())
        daterange = Q(date__gte=self.dbsr_startdate) & Q(date__lte=self.dbsr_enddate)


        msgs = Message.objects.filter(contact__types__in=self.worker_types).filter(locations).filter(daterange).distinct().order_by('-date')

      
        if search_key and search_key.strip():
            stripped = search_key.strip();
            search = Q(text__icontains=stripped) |\
            Q(connection__identity__icontains=stripped) |\
            Q(contact__name__icontains=stripped)
            msgs = Message.objects.filter(locations).filter(daterange).filter(search).distinct().order_by('-date')

        table = []


        if not page:
            page = 1
        
            
        paginator = Paginator(msgs, 200)
        try:
            messages = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            messages = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            messages = paginator.page(paginator.num_pages)

        counter = messages.start_index()
        for msg in messages.object_list:
            date = str(msg.date)[:-4]
            clinic = get_clinic_or_default(msg.contact)
            direction = msg.direction
            name = msg.contact.name if msg.contact else None
            phone = msg.connection.identity
            type = ",".join(type.name for type in msg.contact.types.all())
            text = msg.text
            text =self.get_filtered_message(text)
            table.append([counter,date,clinic, direction,\
                      name, type, phone, text])
            counter = counter + 1
     
        table.insert(0, ['  #', '  Date', '  Clinic', 'Direction', 'Who', 'Worker type','Phone number',
                     'Text'])
        messages_number=messages.number
        messages_has_previous = messages.has_previous()
        messages_has_next = messages.has_next()
        messages_paginator_num_pages = messages.paginator.num_pages
        return table, messages_paginator_num_pages, messages_number, messages_has_next, messages_has_previous
    
