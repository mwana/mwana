import datetime
"""
Some data to represent formated sent results reports for the province,
it's district and facilities
"""
today = datetime.datetime.today()
month = today.month
startdate = datetime.date(today.year, month, 1)
enddate = datetime.date(today.year, month + 1, 1) - datetime.timedelta(days = 1)
startdate = startdate.strftime("%d/%m/%Y")
enddate = enddate.strftime("%d/%m/%Y")

mibenge_report1 = """SENT SAMPLES
Mibenge Clinic
%(date1)s to %(date2)s
Detected;1
NotDetected;3
Rejected;1
TT;5""" % {"date1" : startdate, "date2" : enddate}

central_clinc_rpt = """SENT SAMPLES
Central Clinic
%(date1)s to %(date2)s
Detected;1
NotDetected;1
Rejected;0
TT;2""" % {"date1" : startdate, "date2" : enddate}

mansa_report1 = """SENT SAMPLES
Mansa District
%(date1)s to %(date2)s
Detected;1
NotDetected;1
Rejected;0
TT;2""" % {"date1" : startdate, "date2" : enddate}

samfya_report1 = """SENT SAMPLES
Samfya District
%(date1)s to %(date2)s
Detected;1
NotDetected;3
Rejected;1
TT;5""" % {"date1" : startdate, "date2" : enddate}

province_report1 = """SENT SAMPLES
Luapula Province
01/06/2010 to 30/06/2010
Detected;2
NotDetected;4
Rejected;1
TT;7"""

province_report2 = """SENT SAMPLES
Luapula Province
%(date1)s to %(date2)s
Detected;2
NotDetected;4
Rejected;1
TT;7""" % {"date1" : startdate, "date2" : enddate}