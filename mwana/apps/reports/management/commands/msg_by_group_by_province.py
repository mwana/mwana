# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.broadcast.models import BroadcastMessage
from datetime import datetime
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from mwana.const import get_district_type
from mwana.const import get_province_type
from mwana.const import get_zone_type
from rapidsms.contrib.messagelog.models import Message

class Command(LabelCommand):
    help = "Prints help requests per province in a given period."
    args = "<Start year> <End year>"
    label = 'valid years'

    def handle(self, * args, ** options):
        if len(args) != 2:
            raise CommandError('Please specify 2 %s' % self.label)

        if not (args[0].isdigit() and args[1].isdigit()):
            raise CommandError('Please specify 2 %s' % self.label)

        process(int(args[0]), int(args[1]))

    def __del__(self):
        pass


def who_received(result, date):
    # @type result Result
    req_id = result.requisition_id
    status = result.get_result_display()
    result_message = "%s;%s" % (req_id, status)

    msgs = Message.objects.filter(date__year=date.year, date__month=date.month, date__day=date.day, direction='O', text__contains=result_message)
    return ",".join("%s (%s)" % (msg.contact.name, msg.connection.identity if msg.contact else "") for msg in msgs)


def get_province(location):
    # @type location Location
    if location.type == get_zone_type():
        return location.parent.parent.parent    
    elif location.type == get_district_type():
        return location.parent
    elif location.type == get_province_type():
        return location
    else:
        return location.parent.parent

def process(start_year, end_year):
    class Expando:
        pass
    
    helps = []
    start = datetime(start_year, 1, 1)
    _end = datetime(end_year + 1, 1, 1)
    groups = [i[0] for i in BroadcastMessage.objects.all().values_list('group').distinct()]
    
    for group in groups:
        print '\n_______ MSG', group, '_________', start_year, 'to', end_year
        for msg in Message.objects.filter(text__istartswith="msg %s"% group, date__gte=start).filter(date__lt=_end):
            expando = Expando()
            # @type hr HelpRequest
            if msg.contact:
                expando.province = get_province(msg.contact.location).name
            else:
                expando.province = "Unknown"

            expando.year = msg.date.year
            expando.group = group
            helps.append(expando)
        for province in sorted(set(ex.province for ex in helps)):
            if province in ['Support Province', 'Training Province']:
                continue
            print province, ",", len(filter(lambda x: x.province == province and x.year in range(start_year, end_year + 1), helps))
          