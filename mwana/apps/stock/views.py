# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.stock.models import Transaction
from mwana.apps.stock.models import StockAccount
from mwana.apps.stock.models import Stock
from datetime import date
from datetime import timedelta
from mwana.apps.reports.utils.htmlhelper import get_stock_selector_grid
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html

from mwana.apps.reports.utils.facilityfilter import user_facilities

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.reports.views import read_request
from mwana.apps.reports.utils.htmlhelper import read_date_or_default
from mwana.const import MWANA_ZAMBIA_START_DATE

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.views import read_request
from mwana.apps.reports.utils.htmlhelper import *

class TransactedStock:
    pass

def stock(request):
    today = date.today()
    
    startdate1 = read_date_or_default(request, 'startdate', today - timedelta(days=30))
    enddate1 = read_date_or_default(request, 'enddate', today)
    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, MWANA_ZAMBIA_START_DATE), date.today())

    facilities = user_facilities(current_user=request.user, group=None, province=None, district=None, facility=None)
    
#    rpt_provinces = read_request(request, "rpt_provinces")
    selected_stock = None
    try:
        selected_stock = Stock.objects.filter(id__in=map(int, dict(request.POST).get("_select_stock", ['-1'])))
    except KeyError, e:
        logger.warn("KeyError: %s" % e)

    rpt_districts = read_request(request, "rpt_districts")
    stocks = Stock.objects.all()
    stockAccounts = StockAccount.objects.filter(location__in=facilities)
    stockAccountsWithData = StockAccount.objects.filter(location__in=facilities, amount__gt=0)
    supplied_stock = []
    for sa in StockAccount.objects.filter(account_transaction__date__gte=start_date).filter(account_transaction__date__lt=end_date + timedelta(days=1)).distinct():
        ss = TransactedStock()
        # @type sa StockAccount
        ss.stock_account = sa
        ss.threshold_level = (sa.threshold(start_date) or 0 + sa.threshold(end_date) or 0)/2
        ss.supplied_amount = sa.supplied(start_date, end_date)
        supplied_stock.append(ss)
    
    dispensed_stock = []
    for sa in StockAccount.objects.filter(transaction__in=
            Transaction.objects.filter(date__gte=start_date).\
            filter(date__lt=end_date + timedelta(days=1))
            ).distinct():
        es = TransactedStock()
        # @type sa StockAccount
        es.stock_account = sa
        es.threshold_level = (sa.threshold(start_date) or 0 + sa.threshold(end_date) or 0)/2
        es.dispensed_amount = sa.expended(start_date, end_date)
        dispensed_stock.append(es)

    return render_to_response('stock/stock.html',
                              {
                              "fstart_date": start_date.strftime("%Y-%m-%d"),
                              "fend_date": end_date.strftime("%Y-%m-%d"),
                              "fstart_date2": start_date.strftime("%d %b %Y"),
                              "fend_date2": end_date.strftime("%d %b %Y"),
                              "stock_selection_grid": get_stock_selector_grid("stock_selection_grid", Stock.objects.all().order_by("name"), selected_stock, 1),
#                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", get_rpt_provinces(request.user), rpt_provinces),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", get_rpt_districts(request.user), rpt_districts).replace("All", "------------"),
                              "facilities": facilities,
                              "stocks": stocks,
                              "stockAccounts": stockAccounts,
                              "supplied_stock": supplied_stock,
                              "dispensed_stock": dispensed_stock,
                              "districts_with_data": ", ".join(list(set([sa.location.parent.name for sa in stockAccountsWithData]))),
                              }, context_instance=RequestContext(request)
                              )