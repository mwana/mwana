# vim: ai ts=4 sts=4 et sw=4
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.views.generic import list_detail

from mwana.apps.nutrition.views import export


def remindi(request):
    template_name = "remindmi/summaries.html"
    # get context values here.
    mymessage = "RemindMi summaries"
