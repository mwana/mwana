# vim: ai ts=4 sts=4 et sw=4
from __future__ import absolute_import
from datetime import date
import logging
import json

from django.db.models import Count
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.monitor.models import MonitorSample
from rapidsms.router import send
from rapidsms.models import Contact

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def test(param):
    return 'The test task executed with argument "%s" ' % param


def year():
    return date.today().year


def month():
    return date.today().month


def day():
    return date.today().day


def get_payload_data():
    p = Payload.objects.filter(incoming_date__year=year(),
                               incoming_date__month=month(),
                               incoming_date__day=day()).\
        values("source").annotate(Count('id'))
    return "\n".join(entry['source'] + ": " + str(
        entry['id__count']) for entry in p)


def get_results_data():
    results = Result.objects.filter(verified=True)
    sent_today = results.filter(notification_status='sent',
                                result_sent_date__year=year(),
                                result_sent_date__month=month(),
                                result_sent_date__day=day()).count()
    new = results.filter(notification_status='new').count()
    notified = results.filter(notification_status='notified').count()
    unsynced = get_unsynced_results()

    return "New: %s\nNotified: %s\nSent: %s\nUnsynced: %s" % (new, notified,
                                                              sent_today,
                                                              unsynced)


@shared_task
def send_monitor_report():
    logger.info('sending monitoring information to support staff')

    admins = Contact.active.filter(is_help_admin=True,
                                   monitormessagerecipient__receive_sms=True)

    if not admins:
        logger.warning('No admins to receive data to were found in system')
        return
    message = "Payloads:\n%s;\nResults:\n%s" % (get_payload_data(),
                                                get_results_data())

    for admin in admins:
        send([admin.default_connection], message)


@shared_task
def get_monitor_samples(source_lab, init=False):
    labs = ['lilongwe/pih', 'lilongwe/kch', 'blantyre/dream',
            'blantyre/queens', 'zomba/zch', 'mzimba/mdh',
            'mzuzu/central']
    if init:
        payloads = Payload.objects.filter(source__in=labs,
                                          incoming_date__year=year(),
                                          incoming_date__month=month())
    else:
        payloads = Payload.objects.filter(source__in=labs,
                                          incoming_date__year=year(),
                                          incoming_date__month=month(),
                                          incoming_date__day=day())
    all_results = Result.objects.all()
    synced_results = dict(
        [(r.sample_id, r.arrival_date) for r in all_results])
    data = {}
    unsynced = 0
    for p in payloads:
        data = json.loads(p.raw)
        if 'samples' in data and hasattr(data['samples'], '__iter__'):
            for sample in data['samples']:
                sample_id = sample['id']
                if sample_id in synced_results:
                    status = 'synced'
                    result_obj = all_results.get(sample_id=sample_id)
                else:
                    status = 'pending'
                    unsynced += 1
                m_sample, created = MonitorSample.objects.get_or_create(
                    sample_id=sample_id, hmis=sample['fac'])
                m_sample.status = status
                m_sample.payload = p
                m_sample.result = result_obj
                m_sample.raw = sample
                m_sample.save()
    if not init:
        return unsynced


def get_unsynced_results():
    get_monitor_samples()
