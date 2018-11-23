# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.stock import views

urlpatterns = patterns('',
    url(r"^$", views.stock, name="stock"),
    url(r"^wsm/$", views.wsm_select_location, name="wsm_select_location"),
    url(r"^wsm/create$", views.wsm_create, name="wsm_create"),
    url(r"^wsm/save$", views.wsm_save, name="wsm_save"),
)
