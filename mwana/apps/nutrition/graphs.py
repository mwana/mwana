# vim: ai ts=4 sts=4 et sw=4
from __future__ import division
from decimal import Decimal

from django.db.models import Q

from mwana.apps.nutrition.models import Assessment


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

    def percent(self, num=None, den=None):
        if num is None:
            return float(0)
        elif den is None:
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

    def update_underweight_data(self, fac_asses):
        """  Updates underweight status counts given a filtered queryset"""
        # update raw values data
        self.underweight_data[0].append(fac_asses.filter(Q(underweight='V')).count())
        self.underweight_data[1].append(fac_asses.filter(Q(underweight='T')).count())
        self.underweight_data[2].append(fac_asses.filter(Q(underweight='G')|Q(underweight='L')).count())
        self.underweight_data[3].append(fac_asses.filter(Q(underweight='M')).count())
        self.underweight_data[4].append(fac_asses.filter(Q(underweight='U')).count())
        self.underweight_data[5].append(fac_asses.filter(Q(underweight='S')).count())
        # update percentage data
        den = fac_asses.count()
        self.underweight_data_percent[0].append(self.percent(fac_asses.filter(Q(underweight='V')).count(), den))
        self.underweight_data_percent[1].append(self.percent(fac_asses.filter(Q(underweight='T')).count(), den))
        self.underweight_data_percent[2].append(self.percent(fac_asses.filter(Q(underweight='G')|Q(underweight='L')).count(), den))
        self.underweight_data_percent[3].append(self.percent(fac_asses.filter(Q(underweight='M')).count(), den))
        self.underweight_data_percent[4].append(self.percent(fac_asses.filter(Q(underweight='U')).count(), den))
        self.underweight_data_percent[5].append(self.percent(fac_asses.filter(Q(underweight='S')).count(), den))

    def update_stunting_data(self, fac_asses):
        """  Updates stunting status counts given a queryset"""
        # update raw values data
        self.stunting_data[0].append(fac_asses.filter(Q(stunting='V')).count())
        self.stunting_data[1].append(fac_asses.filter(Q(stunting='T')|Q(stunting='G')|Q(stunting='L')).count())
        self.stunting_data[2].append(fac_asses.filter(Q(stunting='M')).count())
        self.stunting_data[3].append(fac_asses.filter(Q(stunting='U')).count())
        self.stunting_data[4].append(fac_asses.filter(Q(stunting='S')).count())
        # update percentage data
        den = fac_asses.count()
        self.stunting_data_percent[0].append(self.percent(fac_asses.filter(Q(stunting='V')).count(), den))
        self.stunting_data_percent[1].append(self.percent(fac_asses.filter(Q(stunting='T')|Q(stunting='G')|Q(stunting='L')).count(), den))
        self.stunting_data_percent[2].append(self.percent(fac_asses.filter(Q(stunting='M')).count(), den))
        self.stunting_data_percent[3].append(self.percent(fac_asses.filter(Q(stunting='U')).count(), den))
        self.stunting_data_percent[4].append(self.percent(fac_asses.filter(Q(stunting='S')).count(), den))

    def update_wasting_data(self, fac_asses):
        """  Updates wasting status count given a queryset and status"""
        # update raw values data
        self.wasting_data[0].append(fac_asses.filter(Q(wasting='V')).count())
        self.wasting_data[1].append(fac_asses.filter(Q(wasting='G')|Q(wasting='L')|Q(wasting='T')).count())
        self.wasting_data[2].append(fac_asses.filter(Q(wasting='M')).count())
        self.wasting_data[3].append(fac_asses.filter(Q(wasting='U')).count())
        self.wasting_data[4].append(fac_asses.filter(Q(wasting='S')).count())
        # update percentage data
        den = fac_asses.count()
        self.wasting_data_percent[0].append(self.percent(fac_asses.filter(Q(wasting='V')).count(), den))
        self.wasting_data_percent[1].append(self.percent(fac_asses.filter(Q(wasting='G')|Q(wasting='L')|Q(wasting='T')).count(), den))
        self.wasting_data_percent[2].append(self.percent(fac_asses.filter(Q(wasting='M')).count(), den))
        self.wasting_data_percent[3].append(self.percent(fac_asses.filter(Q(wasting='U')).count(), den))
        self.wasting_data_percent[4].append(self.percent(fac_asses.filter(Q(wasting='S')).count(), den))
        
    def get_facilities_data(self):
        """Get facility data for each active facility in the district"""
        active_district_facilities = self.get_active_district_facilities()
        district = self.district
        weight_captured = {}
        height_captured = {}        
        muac_captured = {}
        if active_district_facilities[district]:
            for facility in active_district_facilities[district]:
                fac_asses = self.asses.filter(healthworker__location__parent__name=facility)
                weight_captured[facility] = fac_asses.exclude(underweight='N').count()
                height_captured[facility] = fac_asses.exclude(stunting='N').count()
#                muac_captured[facility] = 
                self.update_underweight_data(fac_asses) 
                self.update_stunting_data(fac_asses) 
                self.update_wasting_data(fac_asses)

            facility_locations = active_district_facilities[district]
        # return facilities data
        self.graph_data['weight_count'] = weight_captured
        self.graph_data['height_count'] = height_captured
        self.graph_data['muac_count'] = muac_captured
        self.graph_data['weight_data'] = self.underweight_data
        self.graph_data['stunt_data'] = self.stunting_data
        self.graph_data['wasting_data'] = self.wasting_data
        self.graph_data['locations'] = facility_locations
        self.graph_data['weight_data_percent'] = self.underweight_data_percent
        self.graph_data['stunt_data_percent'] = self.stunting_data_percent
        self.graph_data['wasting_data_percent'] = self.wasting_data_percent
        return self.graph_data

    def get_districts_data(self):
        """Get district data for each active district in the country"""
        district_weight_captured = {}
        district_height_captured = {}
        district_muac_captured = {}
        district_locations = []
        for district in self.DISTRICTS:
            district_asses = self.asses.filter(healthworker__location__parent__parent__name=district)
            if district_asses.count() != 0:
                district_weight_captured[district] = district_asses.exclude(underweight='N').count()
                district_height_captured[district] = district_asses.exclude(stunting='N').count()
                self.update_underweight_data(district_asses) 
                self.update_stunting_data(district_asses) 
                self.update_wasting_data(district_asses)
                district_locations.append(district)
        # return district data
        self.graph_data['weight_count'] = district_weight_captured
        self.graph_data['height_count'] = district_height_captured
        self.graph_data['muac_count'] = district_muac_captured
        self.graph_data['weight_data'] = self.underweight_data
        self.graph_data['stunt_data'] = self.stunting_data
        self.graph_data['wasting_data'] = self.wasting_data
        self.graph_data['locations'] = district_locations
        self.graph_data['weight_data_percent'] = self.underweight_data_percent
        self.graph_data['stunt_data_percent'] = self.stunting_data_percent
        self.graph_data['wasting_data_percent'] = self.wasting_data_percent
        return self.graph_data

