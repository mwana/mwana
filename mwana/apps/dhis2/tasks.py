# vim: ai ts=4 sts=4 et sw=4
# import requests
import datetime
from celery import task

from mwana.apps.dhis2.models import Indicator, Submission


@task
def generate_and_send_to_dhis2():
    for indicator in Indicator.objects.all():
        indicator.value = execfile(indicator.rule)
        indicator.dhis2_id = query_id(indicator.location)
        indicator.save()
        submission = Submission.objects.create(
            indicator=indicator, status='new')
        sent = submit_to_dhis2(indicator)
        if sent:
            submission.date_sent = datetime.datetime.now()
            submission.status = 'sent'
            submission.save()


def submit_to_dhis2(indicator):
    pass


def query_id(location):
    pass


@task
def generate_indicators():
    pass
