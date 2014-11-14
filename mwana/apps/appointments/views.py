from __future__ import unicode_literals


from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import TemplateView

from django_tables2 import RequestConfig

from .unicsv import UnicodeCSVWriter
from .forms import AppointmentFilterForm
from .tables import ApptTable


class AppointmentMixin(object):
    """Allow filtering by"""
    @method_decorator(permission_required('appointments.view_appointment'))
    def dispatch(self, request, *args, **kwargs):
        self.form = AppointmentFilterForm(request.GET)
        self.items = self.form.get_items()
        return super(AppointmentMixin, self).dispatch(request, *args, **kwargs)


class AppointmentList(AppointmentMixin, TemplateView):
    """Displays a paginated lits of appointments."""
    template_name = 'appointments/appointment_list.html'
    table_template_name = 'django_tables2/bootstrap-tables.html'
    items_per_page = 10

    def get_table(self):
        table = ApptTable(self.items, template=self.table_template_name)
        paginate = {'per_page': self.items_per_page}
        RequestConfig(self.request, paginate=paginate).configure(table)
        return table

    def get_context_data(self, *args, **kwargs):
        return {
            'form': self.form,
            'table': self.get_table()
        }


class CSVAppointmentList(AppointmentMixin, View):
    """Export filtered reports to a CSV file."""
    # Fields to include in the csv, in order.
    filename = 'appointments'

    def get_table(self):
        table = ApptTable(self.items)
        RequestConfig(self.request).configure(table)
        return table

    def get(self, request, *args, **kwargs):
        if not self.form.is_valid():
            url = reverse('appointment_list')
            if request.GET:
                url = '{0}?{1}'.format(url, request.GET.urlencode())
            return HttpResponseRedirect(url)

        response = HttpResponse(content_type='text/csv')
        content_disposition = 'attachment; filename=%s.csv' % self.filename
        response['Content-Disposition'] = content_disposition
        writer = UnicodeCSVWriter(response)
        writer.writerows(self.get_data())
        return response

    def get_data(self):
        table = self.get_table()
        columns = [x.title() for x in table.columns.names()]
        rows = [columns, ]
        for item in table.rows:
            cells = [x for x in item]
            row = []
            for cell in cells:
                row.append(cell)
            rows.append(row)
        return rows
