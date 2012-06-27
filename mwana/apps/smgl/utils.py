#Values that are used to indicate 'no answer' in fields of a form (especially in the case of optional values)
import datetime
NONE_VALUES = ['none', 'n', None]

class DateFormatError(ValueError):  pass
    
def get_date(form, day_field, month_field, year_field):
    parts = [form.xpath('form/%s' % field) for field in (day_field, month_field, year_field)]
    for p in parts:
        if p in NONE_VALUES:
            return None
    try:
        intparts = [int(p) for p in parts]
    except ValueError:
        raise DateFormatError("Not all date parts were valid numbers!")
    
    dd, mm, yy = intparts
    try:
        return datetime.date(yy,mm,dd)
    except ValueError as e:
        raise DateFormatError(str(e))
    
