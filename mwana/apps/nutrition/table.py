# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

import django_tables2 as tables

from models import Assessment


H4A = dict(Assessment.HEIGHT_FOR_AGE_CHOICES)
W4A = dict(Assessment.WEIGHT_FOR_AGE_CHOICES)
W4H = dict(Assessment.WEIGHT_FOR_HEIGHT_CHOICES)
MUAC = dict(Assessment.MUAC_CHOICES)

class AssessmentTable(tables.Table):
    date = tables.Column(verbose_name='Date Submitted')
    location = tables.Column(verbose_name='Facility')
    interviewer_name = tables.Column(verbose_name='Interviewer Name')
    child_id = tables.Column()
    sex = tables.Column()
    date_of_birth = tables.Column()
    age_in_months = tables.Column(verbose_name='Age')
    height = tables.Column()
    weight = tables.Column()
    oedema = tables.Column()
    muac = tables.Column(verbose_name='MUAC')
    muac_status = tables.Column(verbose_name='MUAC Status')
    height4age = tables.Column(verbose_name='Height for age z-score')
    h4astatus = tables.Column(verbose_name='Height for age status')
    weight4age = tables.Column(verbose_name='Weight for age z-score')
    w4astatus = tables.Column(verbose_name='Weight for age status')
    weight4height = tables.Column(verbose_name='Weight for height z-score')
    w4hstatus = tables.Column(verbose_name='Weight for Height Status')
    human_status = tables.Column(verbose_name='Data Quality')

    def render_date(self, value):
        return value.strftime("%Y-%m-%d")

    def render_muac_status(self, value):
        return MUAC[value]

    def render_w4astatus(self, value):
        return W4A[value]

    def render_h4astatus(self, value):
        return H4A[value]

    def render_w4hstatus(self, value):
        return W4H[value]

