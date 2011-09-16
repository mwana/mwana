# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

import django_tables2 as tables


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
    height4age = tables.Column(verbose_name='Height for age z-score')
    weight4age = tables.Column(verbose_name='Weight for age z-score')
    weight4height = tables.Column(verbose_name='Weight for height z-score')
    human_status = tables.Column(verbose_name='Data Quality')

    def render_date(self, value):
        return value.strftime("%Y-%m-%d")

