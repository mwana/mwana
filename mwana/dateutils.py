# vim: ai ts=4 sts=4 et sw=4

from datetime import timedelta

def week_start(p_date):
    return p_date - timedelta(days=p_date.weekday() + 1)


def weekend(p_date):
    return p_date - timedelta(days=p_date.weekday() - 5)


def week_of_year(p_date):
    return int(p_date.strftime('%U'))
