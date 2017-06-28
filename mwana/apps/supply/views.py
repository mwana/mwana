# vim: ai ts=4 sts=4 et sw=4
# Create your views here.
from mwana.apps.supply.forms import SupplyRequestForm
from mwana.apps.supply.models import SupplyRequest
from datetime import datetime
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods, require_GET
from mwana.apps.locations.models import Location
from rapidsms.utils import web_message
from rapidsms.contrib.messaging.utils import send_message
from django.template import RequestContext
from django.shortcuts import render_to_response
#from django.contrib.auth.views import context_instance

@require_GET
def dashboard(request):
    """Supply dashboard"""
    active_requests = SupplyRequest.active().order_by("-created").order_by("location")
    locations = set((req.location for req in active_requests))
    for location in locations:
        location.active_requests = active_requests.filter(location=location)
    return render_to_response( "supply/dashboard.html", 
                              {"active_requests": active_requests,
                               "locations": locations },
                               context_instance=RequestContext(request))

@require_http_methods(["GET", "POST"])
def request_details(request, request_pk):
    """Supply request details view"""
    sreq = get_object_or_404(SupplyRequest, id=request_pk)
    
    if request.method == "POST":
        original_status = sreq.status
        form = SupplyRequestForm(request.POST, instance=sreq)
        if form.is_valid():
            sreq = form.save(commit=False)
            sreq.modified = datetime.utcnow()
            sreq.save()
            if sreq.status != original_status and \
               sreq.requested_by and \
               sreq.requested_by.default_connection:
                # if the status has changed, let's send a message
                # to the original requester so they know things are 
                # proceeding.
                text = ("Your request for more %(supply)s at %(loc)s has been updated! " +\
                        "The new status is: %(status)s.") % \
                            {"supply": sreq.type.name, 
                             "loc":    sreq.location.name, 
                             "status": sreq.get_status_display().upper()}
                send_message(sreq.requested_by.default_connection, text)

            return web_message(request,
                               "Supply request %d status set to %s" % \
                               (sreq.pk, sreq.get_status_display()),
                               link=reverse("supply_dashboard"))
        
    elif request.method == "GET":
        form = SupplyRequestForm(instance=sreq)
    
    return render_to_response("supply/single_request.html", 
                                  {"sreq": sreq, "form": form},
                                  context_instance=RequestContext(request))

@require_GET
def location_details(request, location_pk):
    """Supply location details view"""
    loc = get_object_or_404(Location.objects.select_related(depth=3), 
                            pk=location_pk)
    
    # this is sneaky, but allows us to access this list from
    # template tags without doing extra querying.
    loc.active_requests = SupplyRequest.active().filter(location=loc)
    return render_to_response("supply/single_location.html", 
                              {"location": loc} ,
                              context_instance=RequestContext(request))
    
