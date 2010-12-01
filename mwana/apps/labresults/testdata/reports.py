import datetime
"""
Some data to represent formated sent results reports for the province,
it's district and facilities
"""
today = datetime.datetime.today()
month = today.month
next_month = month < 12 and month + 1 or 1
next_month_year = month < 12 and today.year or today.year + 1
startdate = datetime.date(today.year, month, 1)
enddate = datetime.date(next_month_year, next_month, 1) - datetime.timedelta(days = 1)
startdate = startdate.strftime("%d/%m/%Y")
enddate = enddate.strftime("%d/%m/%Y")

mibenge_report1 = """SENT RESULTS
Mibenge Clinic
%(date1)s to %(date2)s
Detected;1
NotDetected;3
Rejected;1
TT;5""" % {"date1" : startdate, "date2" : enddate}

central_clinc_rpt = """SENT RESULTS
Central Clinic
%(date1)s to %(date2)s
Detected;1
NotDetected;1
Rejected;0
TT;2""" % {"date1" : startdate, "date2" : enddate}

mansa_report1 = """SENT RESULTS
Mansa District
%(date1)s to %(date2)s
Detected;1
NotDetected;1
Rejected;0
TT;2""" % {"date1" : startdate, "date2" : enddate}

samfya_report1 = """SENT RESULTS
Samfya District
%(date1)s to %(date2)s
Detected;1
NotDetected;3
Rejected;1
TT;5""" % {"date1" : startdate, "date2" : enddate}

province_report1 = """SENT RESULTS
Luapula Province
%(date1)s to %(date2)s
Detected;2
NotDetected;4
Rejected;1
TT;7""" % {"date1" : startdate, "date2" : enddate}

province_report2 = """SENT RESULTS
Luapula Province
%(date1)s to %(date2)s
Detected;2
NotDetected;4
Rejected;1
TT;7""" % {"date1" : startdate, "date2" : enddate}