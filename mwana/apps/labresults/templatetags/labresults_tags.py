#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import template
register = template.Library()


@register.inclusion_tag('labresults/templatetags/labresults_map.html')
def render_location(location):
    return { "location": location }
