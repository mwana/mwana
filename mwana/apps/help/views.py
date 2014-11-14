# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.remindmi.views import FilteredSingleTableView

from mwana.apps.help.models import HelpRequest
from .filters import HelpFilter
from .tables import HelpRequestTable


class HelpRequestList(FilteredSingleTableView):
    model = HelpRequest
    table_class = HelpRequestTable
    template_name = 'help/request_list.html'
    filter_class = HelpFilter
    queryset = HelpRequest.objects.all()
