# vim: ai ts=4 sts=4 et sw=4

from django.core.management.base import LabelCommand
from mwana.apps.labresults.models import Result
from rapidsms.contrib.messagelog.models import Message

class Command(LabelCommand):
    def handle(self, * args, ** options):
        process()

    def __del__(self):
        pass


def who_received(result, date):
    # @type result Result
    req_id = result.requisition_id
    status = result.get_result_display()
    result_message = "%s;%s" % (req_id, status)

    msgs = Message.objects.filter(date__year=date.year, date__month=date.month, date__day=date.day, direction='O', text__contains=result_message)
    return ",".join("%s (%s)" % (msg.contact.name, msg.connection.identity if msg.contact else "") for msg in msgs)

def printer(result, date):
    # @type result Result
    req_id = result.requisition_id
    status = result.get_result_display()

    msgs = Message.objects.filter(date__year=date.year, date__month=date.month,
    date__day=date.day, direction='O', text__contains = status
    ).filter(text__contains='Patient ID: '+ req_id)
    return ",".join("%s (%s)" % (msg.contact.name, msg.connection.identity if msg.contact else "") for msg in msgs)


def process():
    clinics =  ['503000', '611016', '613014', '202012', '106098', '706038', '605014', '605016', '204016', '403012', '210030', '204027', '201015']
    results = Result.objects.filter(result='P', result_sent_date__year=2013, clinic__slug__in=clinics).order_by("clinic")

    for res in results:
        # @type res Result
        print "| ".join( str(i) for i in [res.clinic.parent.name, res.clinic.name, "'%s'" % res.requisition_id, res.result_sent_date, res.birthdate, res.sex, who_received(res, res.result_sent_date) or printer(res, res.result_sent_date)])
        