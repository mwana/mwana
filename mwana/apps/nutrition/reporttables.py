from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_tables2_reports.tables import TableReport


from mwana.apps.nutrition.models import Assessment


class AssessmentTable(TableReport):
    facility = tables.Column(verbose_name='Facility',
                             accessor='healthworker.clinic.name')
    district = tables.Column(
        verbose_name='District',
        accessor='healthworker.clinic.parent.name')
    sex = tables.Column(verbose_name='Sex', accessor='patient.gender')
    child_id = tables.Column(verbose_name='Child ID',
                             accessor='patient.code')
    date_of_birth = tables.Column(verbose_name='Date of birth',
                                  accessor='patient.date_of_birth')
    age = tables.Column(verbose_name='Age in months',
                        accessor='patient.age_in_months')

    def render_district(self, value, record):
        if record.healthworker.clinic.parent.parent is not None:
            return record.healthworker.clinic.parent.parent.name
        elif record.healthworker.clinic.parent is not None:
            return record.healthworker.clinic.parent.name
        else:
            return value

    def render_muac(self, value, record):
        klass = record.get_wasting_display().lower()
        return mark_safe('''<span class="%s">%s</span>''' % (klass, value))

    def render_wasting(self, value, record):
        klass = record.get_wasting_display().lower()
        return mark_safe('''<span class="%s">%s</span>''' % (klass, value))

    def render_underweight(self, value, record):
        klass = record.get_underweight_display().lower()
        return mark_safe('''<span class="%s">%s</span>''' % (klass, value))

    # def render_oedema(self, value, record):

    def render_weight4height(self, value, record):
        klass = record.get_wasting_display().lower()
        return mark_safe('''<span class="%s">%s</span>''' % (klass, value))

    def render_weight4age(self, value, record):
        klass = record.get_underweight_display().lower()
        return mark_safe('''<span class="%s">%s</span>''' % (klass, value))

    def render_height4age(self, value, record):
        klass = record.get_stunting_display().lower()
        return mark_safe('''<span class="%s">%s</span>''' % (klass, value))

    def render_stunting(self, value, record):
        klass = record.get_stunting_display().lower()
        return mark_safe('''<span class="%s">%s</span>''' % (klass, value))

    class Meta:
        model = Assessment
        attrs = {'class': "table table-bordered table-condensed"}
        exclude = ('id', 'survey', 'patient')
        sequence = ('date', 'facility', 'district', 'healthworker',
                    'child_id', 'sex', 'date_of_birth',
                    'age', 'height', 'weight', 'oedema',
                    'muac', 'weight4height', 'wasting', 'weight4age',
                    'underweight', 'height4age', 'stunting', 'status',
                    'action_taken')
