# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime
from datetime import timedelta

from mwana.const import get_cba_type
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message


def date_of_last_sms(contact):
    date = None
    try:
        date = Message.objects.filter(direction='I', \
        connection=contact.default_connection).order_by("-date")[0].date
        return date
    except IndexError:pass

    

days_back = 100
today = datetime.today()
date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)


all_cbas = Contact.active.filter(types=get_cba_type()).distinct()

complying_cbas = all_cbas.filter(message__direction="I", message__date__gte=date_back)

defaulting_cbas= set(all_cbas) - set(complying_cbas)


counter = 0
msg_limit = 19
file = open('defaulting_cbas.csv','w')
for contact in all_cbas:
    to_write = "%s,%s,%s,Zone %s,%s"%(contact, contact.default_connection.identity,contact.location.parent.name,contact.location.name, date_of_last_sms(contact) )
    print to_write
    file.write(to_write)
    file.write("\n")


