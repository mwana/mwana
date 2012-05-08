# vim: ai ts=4 sts=4 et sw=4
"""
Find out how many times users retry sending messages after receiving invalid
message
"""

# vim: ai ts=4 sts=4 et sw=4
from datetime import timedelta

from mwana.util import get_clinic_or_default
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact

def my_min(date1, date2):
    if date1 and date2:
        return min(date1, date2)
    elif date1:
        return date1
    elif date2:
        return date2
    else:
        return None

def get_contact(identity):
    try:
        return Contact.objects.filter(default_connection__identity=identity)[0].name
    except:
        return "Unknown"
    
def get_clinic(identity):
    try:
        return get_clinic_or_default(get_contact(identity))
    except:
        return "Unknown"

class Retries:
    def get_retries(self):
        invalid_msgs = Message.objects.filter(text__startswith='Invalid Keyword.'
                                              , connection__identity__startswith='+2609').exclude(contact__location__slug='999999'
                                                   ).order_by('date')
        f = open("c:\\output.txt", 'w')
        f2 = open("c:\\output2.txt", 'w')
        for msg in invalid_msgs:
#            if msg.contact:
#                f.write("insert into retries values('%s', '%s', '%s')" % (get_clinic_or_default(msg.contact).name, msg.contact.name, msg.date) + "\n")
#            else:
#                f.write("insert into retries values('%s', '%s', '%s')" % (get_contact(msg.connection.identity),
#                        get_contact(msg.connection.identity), msg.date) + "\n")
            retries = Message.objects.filter(connection=msg.connection,
                                             date__gt=msg.date,
                                             date__lt=my_min(self.next_invalid_date(msg)
                                             , msg.date + timedelta(hours=1)),
                                             direction='I')
            if not retries:
                if msg.contact:
                    f.write("insert into noretries values('%s', '%s', '%s', '%s');" % (get_clinic_or_default(msg.contact).name, msg.contact.name, msg.connection.identity, msg.date.date()) + "\n")
                else:
                    f.write("insert into noretries values('%s', '%s', '%s', '%s');" % (get_contact(msg.connection.identity),
                            get_contact(msg.connection.identity), msg.connection.identity, msg.date.date()) + "\n")
            for msg in retries:
                try:
                    if msg.contact:
                        f.write("insert into retries values('%s', '%s', '%s', '%s');" % (get_clinic_or_default(msg.contact).name, msg.contact.name, msg.connection.identity, msg.date.date()) + "\n")
                    else:
                        f.write("insert into retries values('%s', '%s', '%s', '%s');" % (get_contact(msg.connection.identity),
                                get_contact(msg.connection.identity), msg.connection.identity, msg.date.date()) + "\n")
                except Exception, e:
                    print "error with: %s" % msg.text
                    print "error with: %s" % e
            

        f.close()
    def next_invalid_date(self, msg):
        try:
            return Message.objects.filter(text__startswith='Invalid Keyword.',
                                          connection=msg.connection,
                                          date__gt=msg.date).order_by('date')[0].date
        except:
            return None