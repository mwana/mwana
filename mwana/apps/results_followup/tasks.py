# vim: ai ts=4 sts=4 et sw=4

import logging
from mwana.apps.results_followup.management.commands.create_followup_results import update_viral_load_alert
from mwana.apps.results_followup.management.commands.create_followup_results import update_infant_result_alert

_ = lambda s: s


logger = logging.getLogger('mwana.apps.results_followup.tasks')


def send_email_alerts(router):
    logger.info('Sending email messages')
    update_infant_result_alert()
    update_viral_load_alert()