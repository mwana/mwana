# vim: ai ts=4 sts=4 et sw=4
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from .models import PregnantMother
from .tables import PregnantMotherTable, HistoryTable


def mothers(request):
    mothers_table = PregnantMotherTable(PregnantMother.objects.all(),
                                        request=request)
    return render_to_response(
        "smgl/mothers.html",
        {"mothers_table": mothers_table
        },
        context_instance=RequestContext(request))


def mother_history(request, id):
    mother = get_object_or_404(PregnantMother, id=id)
    # TODO: aggregate the messages for a mother into a
    messages = mother.get_all_messages()
    return render_to_response(
        "smgl/mother_history.html",
        {"mother": mother,
          "history_table": HistoryTable(messages,
                                        request=request)
        },
        context_instance=RequestContext(request))
