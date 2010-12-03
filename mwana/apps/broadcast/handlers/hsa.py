# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.broadcast.handlers.cba import CBAHandler


class HSAHandler(CBAHandler):
    
    group_name = "HSAs"
    keyword = "HSA"
