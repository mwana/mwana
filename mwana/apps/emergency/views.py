# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.remindmi.views import FilteredSingleTableView

from mwana.apps.emergency.models import FloodReport
from .filters import FloodFilter
from .tables import FloodReportTable


class FloodReportList(FilteredSingleTableView):
    model = FloodReport
    table_class = FloodReportTable
    template_name = 'emergency/report_list.html'
    filter_class = FloodFilter
    queryset = FloodReport.objects.all()
