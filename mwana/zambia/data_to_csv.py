import csv
from mwana.apps.reminders.models import PatientEvent
from numpy import std

def makeithappen():
    patientevents = PatientEvent.objects.filter(patient__location__parent__name='Kambwali').filter(date__gte='2010-10-01')
    mywriter = csv.writer(open('results.csv', 'wb'), delimiter=',')
    titles = ['id', 'Name', 'Date', 'Date_Logged', '(Date-Date_Logged) days']
    mywriter.writerow(titles)
    row = []
    for event in patientevents:
        row = [event.id, event.patient.name, str(event.date), str(event.date_logged), str((event.date - event.date_logged.date()).days)]
        mywriter.writerow(row)
        row = []


def resultdt(clinic):
    from mwana.apps.labresults.models import Result
    import csv
    
    june = Result.objects.filter(arrival_date__month=6).filter(payload__source__contains=clinic)
    july = Result.objects.filter(arrival_date__month=7).filter(payload__source__contains=clinic)
    aug = Result.objects.filter(arrival_date__month=8).filter(payload__source__contains=clinic)
    sep = Result.objects.filter(arrival_date__month=9).filter(payload__source__contains=clinic)
    oct = Result.objects.filter(arrival_date__month=10).filter(payload__source__contains=clinic)
    
    months = [june,july,aug,sep,oct]
    
    deltas = []
    avgs = []
    stds = []
    for month in months:
        dt = []
        for result in month:
            delta = (result.arrival_date.date() - result.entered_on).days
            dt.append(delta) 
        avgs.append(average(dt))
        stds.append(std(dt))
        deltas.append(dt)
        
    mywriter = csv.writer(open('results.csv', 'wb'), delimiter=',')
    titles = ['Average June','Average July', 'Average Aug', 'Average Sep', 'Average Oct']
    mywriter.writerow(titles)
    mywriter.writerow(avgs)
    titles = ['Std Deviation for: June','July', 'Aug', 'Sep', 'Oct']
    mywriter.writerow(titles)
    mywriter.writerow(stds)
    mywriter.writerow(['Difference in days for each result, each row = 1 month'])
    
    for dt in deltas:
        mywriter.writerow(dt)
    
        
        
def average(numbers):
    if len(numbers) == 0 : return None
    return sum(numbers) / float(len(numbers))
