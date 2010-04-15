# Create your views here.
from apps.supply.forms import SupplyRequestForm
from apps.supply.models import SupplyRequest
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.templatetags.tabs_tags import register_tab
from django.views.decorators.http import require_http_methods
from rapidsms.contrib.locations.models import Location
from rapidsms.utils import render_to_response, web_message

@register_tab(caption="Supplies")
def dashboard(request):
    """Supply dashboard"""
    active_requests = SupplyRequest.active().order_by("-created").order_by("location")
    locations = set((req.location for req in active_requests))
    for location in locations:
        location.active_requests = active_requests.filter(location=location)
    return render_to_response(request, "supply/dashboard.html", 
                              {"active_requests": active_requests,
                               "locations": locations })

@require_http_methods(["GET", "POST"])
def details(request, request_pk):
    """Supply details view"""
    sreq = get_object_or_404(SupplyRequest, id=request_pk)
    
    if request.method == "POST":
        form = SupplyRequestForm(request.POST, instance=sreq)
        if form.is_valid():
            supply = form.save()
            return web_message(request,
                               "Supply request %d status set to %s" % \
                               (supply.pk, supply.get_status_display()),
                               link=reverse("supply_dashboard"))
        
    elif request.method == "GET":
        form = SupplyRequestForm(instance=sreq)
    
    return render_to_response(request, "supply/single_request.html", 
                                  {"sreq": sreq, "form": form})
    