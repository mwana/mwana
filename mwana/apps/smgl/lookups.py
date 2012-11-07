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
    excludes = {'type__singular__in': ['district', 'Province']}
    search_fields = ('name__icontains', )

    def get_queryset(self):
        qs = self.model._default_manager.get_query_set()
        if self.filters:
            qs = qs.filter(**self.filters)
        if self.excludes:
            qs = qs.exclude(**self.excludes)
        return qs

    def get_query(self, request, term):
        results = super(FacilityLookup, self).get_query(request, term)
        district = request.GET.get('district', '')
        if district:
            district_facilities = []
            for x in results:
                # TODO --> Need this utility when this lookup is implemented
                if get_location_district(x) == district:
                    district_facilities.append(x)
            return district_facilities
        return results

    def get_item_label(self, item):
        return u"%s, %s" % (item.name, item.parent)

registry.register(ProvinceLookup)
registry.register(DistrictLookup)
registry.register(FacilityLookup)
