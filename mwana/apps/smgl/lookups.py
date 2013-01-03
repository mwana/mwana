from selectable.base import ModelLookup
from selectable.registry import registry

from mwana.apps.locations.models import Location

from .utils import get_location_tree_nodes


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
        results = results.order_by('name')
        province = request.GET.get('province', '')
        if province:
            results = results.filter(parent=province)
        return results

    def get_item_label(self, item):
        return u"%s" % (item.name)


class FacilityLookup(ModelLookup):
    model = Location
    exclude = {'type__singular__in': ['district', 'Province', 'Zone', 'Head Office']}
    search_fields = ('name__icontains', )

    def get_queryset(self):
        qs = self.model._default_manager.get_query_set()
        if self.filters:
            qs = qs.filter(**self.filters)
        if self.exclude:
            qs = qs.exclude(**self.exclude)
        return qs

    def get_query(self, request, term):
        results = super(FacilityLookup, self).get_query(request, term)
        results = results.order_by('name')
        district = request.GET.get('district', '')
        if district:
            loc = Location.objects.get(pk=district)
            results = get_location_tree_nodes(loc)
            results = [x for x in results if x.type.singular not in ['Zone', 'Head Office']]
        return results

    def get_item_label(self, item):
        return u"%s" % (item.name)


class ZoneLookup(ModelLookup):
    model = Location
    filters = {'type__singular': 'Zone'}
    search_fields = ('name__icontains', )

    def get_query(self, request, term):
        results = super(ZoneLookup, self).get_query(request, term)
        results = results.order_by('name')
        facility = request.GET.get('facility', '')
        if facility:
            results = results.filter(parent=facility)
        return results

    def get_item_label(self, item):
        return u"%s" % (item.name)

registry.register(ProvinceLookup)
registry.register(DistrictLookup)
registry.register(FacilityLookup)
registry.register(ZoneLookup)
