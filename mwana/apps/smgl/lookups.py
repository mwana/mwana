from selectable.base import ModelLookup
from selectable.registry import registry

from mwana.apps.locations.models import Location


class ProvinceLookup(ModelLookup):
    model = Location
    filters = {'type__singular': 'Province'}
    search_fields = ('name__icontains', )


class DistrictLookup(ModelLookup):
    model = Location
    filters = {'type__singular': 'district'}
    search_fields = ('name__icontains', )

    def get_query(self, request, term):
        results = super(DistrictLookup, self).get_query(request, term)
        province = request.GET.get('province', '')
        if province:
            results = results.filter(parent=province)
        return results

    def get_item_label(self, item):
        return u"%s, %s" % (item.name, item.parent)


class FacilityLookup(ModelLookup):
    model = Location
    filters = {'parent__type__singular': 'district'}
    search_fields = ('name__icontains', )

    def get_query(self, request, term):
        results = super(FacilityLookup, self).get_query(request, term)
        district = request.GET.get('district', '')
        if district:
            results = results.filter(parent=district)
        return results

    def get_item_label(self, item):
        return u"%s, %s" % (item.name, item.parent)

registry.register(ProvinceLookup)
registry.register(DistrictLookup)
registry.register(FacilityLookup)
