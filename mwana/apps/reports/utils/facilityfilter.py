# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.locations.models import Location
from django.db.models import Q

def user_facilities(current_user=None, group=None, province=None, district=None, facility=None):

    facs = Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=current_user)
    if group:
        facs = facs.filter(Q(groupfacilitymapping__group__id=group) | Q(groupfacilitymapping__group__name__iexact=group))

    if facility:
        facs = facs.filter(slug=facility)
    elif district:
        facs = facs.filter(parent__slug=district)
    elif province:
        facs = facs.filter(parent__parent__slug=province)
    return facs


def get_rpt_provinces(user):
    return get_distinct_parents(get_rpt_districts(user))

def get_distinct_parents(locations):
    if not locations:
        return []
    parents = []
    for location in locations:
        parents.append(location.parent)
    return list(set(parents))

def get_rpt_districts(user):
    return get_distinct_parents(Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=user))

def get_rpt_facilities(user):
    return Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=user)




