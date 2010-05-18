
from django import template
register = template.Library()


@register.inclusion_tag('supply/templatetags/supply_map.html')
def render_location(location):
    return { "location": location }
