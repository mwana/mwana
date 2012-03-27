# vim: ai ts=4 sts=4 et sw=4
from __future__ import division
from decimal import Decimal

from django.db.models import Q

from mwana.apps.nutrition.models import Assessment
from mwana.apps.locations.models import Location


class NutritionGraphs(object):
    """Calculate values for nutrition graphs"""

    DISTRICTS = ['Balaka', 'Blantyre', 'Chikwawa', 'Chiradzulu', 'Chitipa', 'Dedza',
                 'Dowa', 'Karonga', 'Kasungu', 'Likoma', 'Lilongwe', 'Machinga', 'Mangochi',
                 'Mchinji', 'Mulanje', 'Mwanza', 'Mzimba', 'Neno', 'Nkhata Bay', 'Nkhotakota',
                 'Nsanje', 'Ntcheu', 'Ntchisi', 'Phalombe', 'Rumphi', 'Salima', 'Thyolo', 'Zomba']

    def __init__(self, assessments=None, district=None):
        self.district = district
        self.asses = assessments
        self.underweight_data = [['Obese'], ['Overweight'], ['Normal'], ['Mild'], ['Moderate'], ['Severe']]
        self.stunting_data = [['Very Tall'],['Normal'],['Mild'], ['Moderate'], ['Severe']]
        self.wasting_data = [['Unusual'],['Normal'],['Mild'], ['Moderate'], ['Severe']]
        self.underweight_data_percent = [['Obese'], ['Overweight'], ['Normal'], ['Mild'], ['Moderate'], ['Severe']]
        self.stunting_data_percent = [['Very Tall'],['Normal'],['Mild'], ['Moderate'], ['Severe']]
        self.wasting_data_percent = [['Unusual'],['Normal'],['Mild'], ['Moderate'], ['Severe']]
        self.graph_data = {}
        self.underweight_table = {}
        self.stunting_table = {}
        self.wasting_table = {}

    def percent(self, num=None, den=None):
        if num is None or num == 0:
            return float(0)
        elif den is None or den == 0:
            return float(0)
        else:
            return 100 * num / den
        
    def get_active_district_facilities(self):
        district_facilities = {}
        for district in self.DISTRICTS:
            zone = Q(healthworker__location__name=district)
            clinic = Q(healthworker__location__parent__name=district)
            dist = Q(healthworker__location__parent__parent__name=district)
            district_data = self.asses.filter(zone|clinic|dist)
            facilities = []
            for i in district_data:
                if i.healthworker.clinic.name not in facilities:
                    facilities.append(i.healthworker.clinic.name)
            district_facilities[district] = [str(unicode(item)) for item in facilities]
        return district_facilities

    def get_population(self, location):
        location = Location.objects.filter(name=location).distinct()
        if location:
            return location[0].population

    def update_underweight_data(self, fac_asses, location):
        """  Updates underweight status counts given a filtered queryset"""
        metric = [fac_asses.filter(underweight='V').count(), fac_asses.filter(underweight='T').count(), fac_asses.filter(Q(underweight='G')|Q(underweight='L')).count(),fac_asses.filter(underweight='M').count(), fac_asses.filter(underweight='U').count(), fac_asses.filter(underweight='S').count()]
        den = fac_asses.count()
        weight_captured = fac_asses.exclude(underweight='N').count()
        # populace = self.get_population(location)
        # efficiency = "%.1f%%" % (self.percent(weight_captured/populace))
        self.underweight_table[location] = []
        self.underweight_table[location].append(weight_captured)
        self.underweight_table[location].append("%")
        i = 0
        while i < len(metric):
            self.underweight_data[i].append(metric[i])
            self.underweight_data_percent[i].append(self.percent(metric[i], den))
            self.underweight_table[location].append("%.1f%%" % (self.percent(metric[i], den)))
            i += 1

    def update_stunting_data(self, fac_asses, location):
        """  Updates stunting status counts given a filtered queryset"""
        metric = [fac_asses.filter(stunting='V').count(), fac_asses.filter(Q(stunting='T') | Q(stunting='G')|Q(stunting='L')).count(),fac_asses.filter(stunting='M').count(), fac_asses.filter(stunting='U').count(), fac_asses.filter(stunting='S').count()]
        den = fac_asses.exclude(stunting='N').count()
        # populace = self.get_population(location)
        # efficiency = "%.1f%%" % (self.percent(den/populace))
        self.stunting_table[location] = []
        self.stunting_table[location].append(den)
        self.stunting_table[location].append("%")
        i = 0
        while i < len(metric):
            self.stunting_data[i].append(metric[i])
            self.stunting_data_percent[i].append(self.percent(metric[i], den))
            self.stunting_table[location].append("%.1f%%" % (self.percent(metric[i], den)))
            i += 1

    def update_wasting_data(self, fac_asses, location):
        """  Updates wasting status counts given a filtered queryset"""
        metric = [fac_asses.filter(wasting='V').count(), fac_asses.filter(Q(wasting='T') | Q(wasting='G')|Q(wasting='L')).count(),fac_asses.filter(wasting='M').count(), fac_asses.filter(wasting='U').count(), fac_asses.filter(wasting='S').count()]
        den = fac_asses.filter(muac__isnull=False).count()
        # populace = self.get_population(location)
        # efficiency = "%.1f%%" % (self.percent(den/populace))        
        self.wasting_table[location] = []
        self.wasting_table[location].append(den)
        self.wasting_table[location].append("%")
        self.wasting_table[location].append(fac_asses.exclude(stunting='N').count())
        i = 0
        while i < len(metric):
            self.wasting_data[i].append(metric[i])
            self.wasting_data_percent[i].append(self.percent(metric[i], den))
            self.wasting_table[location].append("%.1f%%" % (self.percent(metric[i], den)))
            i += 1
        self.wasting_table[location].append(fac_asses.exclude(Q(oedema__isnull=True)|Q(oedema=False)).count())

    def set_graph_data(self, locations):
        """ Set the updated data and return the dict"""
        self.graph_data['weight_table'] = self.underweight_table
        self.graph_data['stunt_table'] = self.stunting_table
        self.graph_data['wasting_table'] = self.wasting_table
        self.graph_data['weight_data'] = self.underweight_data
        self.graph_data['stunt_data'] = self.stunting_data
        self.graph_data['wasting_data'] = self.wasting_data
        self.graph_data['locations'] = locations
        self.graph_data['weight_data_percent'] = self.underweight_data_percent
        self.graph_data['stunt_data_percent'] = self.stunting_data_percent
        self.graph_data['wasting_data_percent'] = self.wasting_data_percent

    def get_facilities_data(self):
        """Get facility data for each active facility in the district"""
        active_district_facilities = self.get_active_district_facilities()
        district = self.district
        if active_district_facilities[district]:
            for facility in active_district_facilities[district]:
                fac_asses = self.asses.filter(healthworker__location__parent__name=facility)
                self.update_underweight_data(fac_asses, facility) 
                self.update_stunting_data(fac_asses, facility) 
                self.update_wasting_data(fac_asses, facility)

            facility_locations = active_district_facilities[district]
        # return facilities data
        self.set_graph_data(facility_locations)
        return self.graph_data

    def get_districts_data(self):
        """Get district data for each active district in the country"""
        district_locations = []
        for district in self.DISTRICTS:
            district_asses = self.asses.filter(healthworker__location__parent__parent__name=district)
            if district_asses.count() != 0:
                self.update_underweight_data(district_asses, district) 
                self.update_stunting_data(district_asses, district) 
                self.update_wasting_data(district_asses, district)
                district_locations.append(district)
        # return district data
        self.set_graph_data(district_locations)
        return self.graph_data


