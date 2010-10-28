#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import datetime
from django.db.models import Q
from mwana import const
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.locations.models import Location
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact

class ReportHandler(KeywordHandler):
    """
    """

    keyword = "report|reports|repot|repots"

#    PATTERN = re.compile(r"^(\w+)(\s+)(.{4,})(\s+)(\d+)$")
    
    PIN_LENGTH = 4     
    MIN_CLINIC_CODE_LENGTH = 3
    MIN_NAME_LENGTH = 1

    HELP_TEXT = "To view a report, send REPORT <CLINIC_CODE> [MONTH]"
    NOT_ELIGIBLE = "I am sorry, you do not have permission to view reports."
        
    def help(self):
        self.respond(self.HELP_TEXT)    

    def handle(self, text):
        b = InputCleaner()
        if not is_eligible_for_results(self.msg.connection):
            self.respond(self.NOT_ELIGIBLE)
            return
        if not text or not text.strip():
            return
        clinic_code = text.split()[0]
        #staff with zeros in case someone just send PP or PPDD
        if b.try_replace_oil_with_011(clinic_code[0:6]).isdigit():
            clinic_code = clinic_code + "00000"
            clinic_code = clinic_code[0:6]
        district_facilities = None
        province_facilities = None
        try:
            location = Location.objects.get(slug__iexact=clinic_code)
            if location.type.slug == 'districts':
                district_facilities = Location.objects.filter(parent=location,
                                                              type__slug__in=
                                                              const.CLINIC_SLUGS)
            elif location.type.slug == 'provinces':
                province_facilities = Location.objects.filter(parent__parent=
                                                              location,
                                                              type__slug__in=
                                                              const.CLINIC_SLUGS)

        except Location.DoesNotExist:
            # maybe it's a district like 403000
            try:
                clinic_code = clinic_code.replace('000', '0')
                district_facilities = Location.objects.filter(slug__startswith=
                                                              clinic_code,
                                                              type__slug__in=
                                                              const.CLINIC_SLUGS)
                location = district_facilities[0].parent
            except IndexError:
                #maybe it's a province like 400000
                try:
                    clinic_code = clinic_code.replace('000', '0')
                    province_facilities = Location.objects.filter(slug__startswith=
                                                                  clinic_code,
                                                                  type__slug__in=
                                                                  const.CLINIC_SLUGS)
                    location = province_facilities[0].parent.parent
                    
                except IndexError:
                    self.respond("Sorry, I don't know about a location with code %(code)s. Please check your code and try again.",
                                 code=clinic_code)
                    return
        text = text.strip()
        text = b.remove_double_spaces(text)
        today = datetime.datetime.today()
        try:
            month = int(b.words_to_digits(text.split()[1][0:3]))
        except (IndexError, TypeError):
            month = today.month
        if month not in range(1, 13):
            month = today.month
        startdate = datetime.datetime(today.year, month, 1)
        if month == 12:
            enddate = datetime.datetime(today.year, 12, 31)
        else:
            enddate = datetime.datetime(today.year, month + 1, 1) - datetime.timedelta(seconds=1)
        report_values = self.get_facility_report(location, startdate, enddate,
                                                 district_facilities,
                                                 province_facilities)

        rpt_header = "SENT RESULTS\n%s\n%s to %s" % (location.name,
                                                     startdate.strftime("%d/%m/%Y"), enddate.strftime("%d/%m/%Y"))
        rpt_data = '\n'.join(key + ";" + str(value) for key, value in
                             report_values.items())
        msg = rpt_header + '\n' + rpt_data         
        
        self.respond(msg)

    def get_msgs_with_live_results(self, startdate, enddate, contacts):
        return Message.objects.filter(Q(date__gt=startdate)
                                          | Q(date=startdate),
                                          Q(date__lt=enddate) | Q(date=enddate),
                                          direction__iexact='O', 
                                          contact__in=contacts,
                                          text__icontains='ected').exclude(
                                          Q(text__icontains='Sample 9999') |
                                          (Q(text__icontains='**** 9990;') &
                                          Q(text__icontains='**** 9991;') &
                                          Q(text__icontains='**** 9992;')))
                                          
    def get_facility_report(self, location, startdate,
                            enddate, district_facilities, province_facilities):
        """
        Returns report values as a dictionary of indicators/values from message
        logs for a given location. Results will be counted twice if received
        twice, ie via CHECK and RESULT
        """
        if province_facilities:
            return self.get_facilities_summed_report(province_facilities,
                                                     startdate, enddate)
        elif district_facilities:
            return self.get_facilities_summed_report(district_facilities,
                                                     startdate, enddate)

        contacts = Contact.objects.filter(location=location)
        msgs = self.get_msgs_with_live_results(startdate, enddate, contacts)

        rejected_results = negative_results = positive_results = 0
        for msg in msgs:
            rejected_results  = rejected_results + msg.text.count(';Rejected')
            negative_results = negative_results + msg.text.count(';NotDetected')
            positive_results = positive_results + msg.text.count(';Detected')

        total = rejected_results + negative_results + positive_results
        results = {'Rejected':rejected_results, 'NotDetected':negative_results,
            'Detected':positive_results, 'TT':total}
        return results

    def get_facilities_summed_report(self, many_locations, startdate, enddate):
        """
        Returns report values as a dictionary of indicators/values from message
        logs for given locations. Results will be counted twice if received
        twice, ie via CHECK and RESULT
        """
        rejected_results = negative_results = positive_results = 0
        for location in many_locations:
            contacts = Contact.objects.filter(location=location)
            msgs = self.get_msgs_with_live_results(startdate, enddate, contacts)
            
            for msg in msgs:
                rejected_results  = rejected_results + msg.text.count(';Rejected')
                negative_results = negative_results + msg.text.count(';NotDetected')
                positive_results = positive_results + msg.text.count(';Detected')

            total = rejected_results + negative_results + positive_results
            results = {'Rejected':rejected_results, 'NotDetected':negative_results,
                'Detected':positive_results, 'TT':total}
        return results

