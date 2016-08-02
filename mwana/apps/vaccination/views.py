# vim: ai ts=4 sts=4 et sw=4

from django.views.decorators.http import require_GET
from django.template import RequestContext
from django.shortcuts import render_to_response
from mwana.apps.locations.models import Location


@require_GET
def dashboard(request):
    locations = Location.objects.filter(supportedlocation__supported=True)
    return render_to_response("vaccination/dashboard.html",
                              {"locations": locations },context_instance=RequestContext(request))

