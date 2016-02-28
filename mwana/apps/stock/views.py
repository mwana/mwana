# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.stock.models import StockTransaction
from mwana.apps.stock.models import Threshold
from mwana.apps.stock.models import StockAccount
from mwana.apps.stock.models import Stock
from datetime import date
from datetime import timedelta
from mwana.apps.reports.utils.htmlhelper import get_stock_selector_grid
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_rpt_districts

from mwana.apps.reports.utils.facilityfilter import user_facilities

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.reports.views import read_request
from mwana.apps.reports.utils.htmlhelper import read_date_or_default
from mwana.const import MWANA_ZAMBIA_START_DATE


from mwana.apps.reports.utils.htmlhelper import read_request
from datetime import date

class TransactedStock:
    pass

def _year_ago(date_param):
    return date(date_param.year - 1, date_param.month, date_param.day)


def can_set_threshold(user):
    if not user:
        return False
    if user.is_active and user.is_superuser:
        return True

    return bool([gum.group.name for gum in user.groupusermapping_set.all() if 'DHO' in gum.group.name])

def stock(request):
    today = date.today()
    
    startdate1 = read_date_or_default(request, 'startdate', today - timedelta(days=30))
    enddate1 = read_date_or_default(request, 'enddate', today)
    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, MWANA_ZAMBIA_START_DATE), date.today())

    facilities = user_facilities(current_user=request.user, group=None, province=None, district=None, facility=None)
    
    selected_stock = None
    selected_stock = Stock.objects.filter(id__in=map(int, dict(request.POST).get("_select_stock", ['-1'])))

    if can_set_threshold(request.user):
        new_threshold_stock = dict(request.POST).get('new_threshold_stock', [None])[0]
        new_threshold_facility = dict(request.POST).get('new_threshold_facility', [None])[0]
        new_threshhold_value = dict(request.POST).get('new_threshhold_value', [None])[0]
        if new_threshold_facility and new_threshold_stock and new_threshhold_value:
            # we don't expect object to exist
            stock_account  = StockAccount.objects.get(location__slug=\
                                                        new_threshold_facility,
                                                        stock__id=int(new_threshold_stock))
            # @type stock_account StockAccount
            if stock_account.current_threshold != int(new_threshhold_value):
                Threshold.objects.create(account=stock_account,
                                            level=int(new_threshhold_value),
                                            start_date=date.today())

    rpt_districts = read_request(request, "rpt_districts")
    stocks = Stock.objects.all()
    stockAccounts = StockAccount.objects.filter(location__in=facilities)
    stockAccountsWithData = StockAccount.objects.filter(location__in=facilities, amount__gt=0)
    supplied_stock = []
    for sa in StockAccount.objects.filter(account_transaction__transaction__date__gte=start_date).filter(account_transaction__transaction__date__lt=end_date + timedelta(days=1)).distinct():
        ss = TransactedStock()
        # @type sa StockAccount
        ss.stock_account = sa
        # This should ideally be calculate using historical dat
        ss.expected_supply_level = sa.expended(_year_ago(start_date), _year_ago(end_date)) or 0
        ss.supplied_amount = sa.supplied(start_date, end_date)
        supplied_stock.append(ss)
    
    dispensed_stock = []
    d_stock_transactions = StockTransaction.objects.exclude(account_from=None).filter(
                        transaction__date__gte=start_date).\
                        filter(transaction__date__lt=end_date + timedelta(days=1)).distinct()
    for sa in (st.account_from for st in d_stock_transactions):
        es = TransactedStock()
        # @type sa StockAccount
        es.stock_account = sa

        # This should ideally be calculate using historical data
        es.expected_dispensed_level = sa.expended(_year_ago(start_date), _year_ago(end_date)) or 0
        
        es.dispensed_amount = sa.expended(start_date, end_date)
        dispensed_stock.append(es)

    selected_facilities = map(str, dict(request.POST).get("_select_facility", ['-1']))

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
                              "selected_facilities": selected_facilities,
                              "stocks": stocks,
                              "stockAccounts": stockAccounts,
                              "supplied_stock": supplied_stock,
                              "dispensed_stock": dispensed_stock,
                              "can_set_threshold": ("%s" % can_set_threshold(request.user)).lower(),
                              "districts_with_data": ", ".join(list(set([sa.location.parent.name for sa in stockAccountsWithData]))),
                              }, context_instance=RequestContext(request)
                              )