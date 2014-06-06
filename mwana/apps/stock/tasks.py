# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.stock.models import LowStockLevelNotification
from mwana.const import get_district_worker_type
from mwana.apps.stock.models import StockAccount
from datetime import date
import logging

from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact
from datetime import date

logger = logging.getLogger(__name__)


def send_stock_below_threshold_notification(router):
    logger.info('In send_stock_below_threshold_notification')

    dhos = Contact.active.filter(types=get_district_worker_type(), location__supported__supported=True)
    if not dhos:
        logger.info('No Staff found to send notifications to')
        return
    
    today = date.today()
    for dho in dhos:
        stock_below_threshold = []
        locations_with_low_stock = set()
        stock_level_per_location = set()
        unique_stock = set()

        for sa in StockAccount.objects.filter(location__parent=dho.location):
            if LowStockLevelNotification.objects.filter(stock_account=sa, level=sa.amount,
            contact=dho, week_of_year=LowStockLevelNotification.week(today)):
                continue
            if sa.amount < sa.current_threshold:
                locations_with_low_stock.add(sa.location)
                stock_below_threshold.append(sa)
                stock_level_per_location.add("%s-%s=%s" % (sa.location.name, sa.stock.code, sa.amount))
                unique_stock.add(sa.stock)


        if not stock_below_threshold:
            continue
        msg_text = ""
        if len(stock_level_per_location) > 3:
            msg_text = "Hi %(name)s. %(num_of_stock)s Stock levels at %(num_of_facs)s facilities have gone too low. " \
                       "Check on the Mwana web tool for details" %({'name': dho.name, 'num_of_stock': len(unique_stock),
                                                                    'num_of_facs': len(locations_with_low_stock)})
        else:
            msg_text = "Hi. Following stock are below thresholds: " + "*** ".join(stock_level_per_location)


        OutgoingMessage(dho.default_connection, msg_text).send()

        for record in stock_below_threshold:
            LowStockLevelNotification.objects.create(stock_account=record, contact=dho, level=record.amount)

     