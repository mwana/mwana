from django.core.urlresolvers import reverse

from djtables import Table, Column
from djtables.column import DateColumn


class PregnantMotherTable(Table):
    created_date = DateColumn(format="Y m d H:i ")
    uid = Column(link=lambda cell: reverse("mother-history", args=[cell.object.id]))
    location = Column()
    edd = DateColumn(format="d/m/Y")
    risks = Column(value=lambda cell: ", ".join([x.upper() \
                                     for x in cell.object.get_risk_reasons()]),
                   sortable=False)

    class Meta:
        order_by = "-created_date"


class HistoryTable(Table):
    date = Column()
    type = Column()
    sender = Column()
    facility = Column()
    message = Column()

    class Meta:
        order_by = "-date"
