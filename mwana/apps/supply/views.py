# Create your views here.
from apps.supply.forms import SupplyRequestForm
from apps.supply.models import SupplyRequest
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.templatetags.tabs_tags import register_tab
from django.views.decorators.http import require_http_methods, require_GET
from rapidsms.contrib.locations.models import Location
from rapidsms.utils import render_to_response, web_message
from datetime import datetime

@register_tab(caption="Supplies")
@require_GET
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
def request_details(request, request_pk):
    """Supply request details view"""
    sreq = get_object_or_404(SupplyRequest, id=request_pk)
    
    if request.method == "POST":
        form = SupplyRequestForm(request.POST, instance=sreq)
        if form.is_valid():
            supply = form.save(commit=False)
            supply.modified = datetime.utcnow()
            supply.save()
            return web_message(request,
                               "Supply request %d status set to %s" % \
                               (supply.pk, supply.get_status_display()),
                               link=reverse("supply_dashboard"))
        
    elif request.method == "GET":
        form = SupplyRequestForm(instance=sreq)
    
    return render_to_response(request, "supply/single_request.html", 
                                  {"sreq": sreq, "form": form})

@require_GET
def location_details(request, location_pk):
    """Supply location details view"""
    loc = get_object_or_404(Location.objects.select_related(depth=3), 
                            pk=location_pk)
    
    # this is sneaky, but allows us to access this list from
    # template tags without doing extra querying.
    loc.active_requests = SupplyRequest.active().filter(location=loc)
    return render_to_response(request, "supply/single_location.html", 
                              {"location": loc} )