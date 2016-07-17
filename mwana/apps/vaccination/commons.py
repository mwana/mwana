# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
import re


class Parser():
    DATE_RE = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4}|\d{2})$")
    PATIENT_ID_RE = re.compile(r"\d+/\d+")

    @classmethod
    def _parse_date(cls, birth_date_str):        
        dob = None
        date_str = re.sub('[. -]', '/', birth_date_str)
        while '//' in date_str:
            date_str = date_str.replace('//', '/')
        for format in ['%d/%m/%y', '%d/%m/%Y']:
            try:
                dob = datetime.strptime(date_str, format).date()
            except ValueError:
                pass
            if dob:
                break
        return dob