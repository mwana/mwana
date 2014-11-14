# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.remindmi.views import FilteredSingleTableView

from mwana.apps.dhis2.models import Submission
from .filters import SubmissionFilter
from .dhis2tables import SubmissionTable


class SubmissionList(FilteredSingleTableView):
    model = Submission
    table_class = SubmissionTable
    template_name = 'dhis2/submission_list.html'
    filter_class = SubmissionFilter
    queryset = Submission.objects.all()
