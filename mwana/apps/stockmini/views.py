# vim: ai ts=4 sts=4 et sw=4
from django.shortcuts import render_to_response
from django.template import RequestContext

from mwana.apps.stockmini.models import StockOnHand


def stock_mini(request):
    stock_on_hand = StockOnHand.objects.all()
    return render_to_response('stock_report.html', {
        'model': "Stock Levels",
        'stock_on_hand': stock_on_hand
    }, context_instance=RequestContext(request))
