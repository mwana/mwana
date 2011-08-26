#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
from django.db import models


class HealthWorker(models.Model):
    HW_STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
    )
    last_updated           = models.DateTimeField(auto_now=True)
    # counter for measurement errors, not poor texting skills
    # incremented only when z-scores indicate unreasonable measurements
    errors                 = models.IntegerField(max_length=5,default=0) 
    status                 = models.CharField(max_length=1,choices=HW_STATUS_CHOICES,default='A')
    interviewer_id          = models.PositiveIntegerField(max_length=10, blank=True, null=True)

    # disabled because the mwana labresults app also provides an alias field
    #alias      = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name  = models.CharField(max_length=30, blank=True)


    def num_messages_sent(self, when=None):
        time_chunks = {
                'today' : datetime.datetime.now().date(),
                'week' : (datetime.datetime.now()-timedelta(weeks=1)),
                'month' : (datetime.datetime.now()-timedelta(days=30)),
                'year' : (datetime.datetime.now()-timedelta(days=365))}
        if when in time_chunks.keys():
                return self.incoming_messages.filter(\
                            received__gte=time_chunks[when]).count()
        else:
            return self.incoming_messages.all().count()

    @classmethod
    def parse_name(klass, flat_name):
        """Given a single string, this function returns a three-string
           tuple containing a suggested alias, first name, and last name,
           via some quite crude pattern matching."""

        patterns = [
            # try a few common name formats.
            # this is crappy but sufficient
            r"([a-z]+)",                       # Adam
            r"([a-z]+)\s+([a-z]+)",            # Evan Wheeler
            r"([a-z]+)\s+[a-z]+\.?\s+([a-z]+)",# Mark E. Johnston
            r"([a-z]+)\s+([a-z]+\-[a-z]+)"     # Erica Kochi-Fabian
        ]

        def unique(in_str, max_length=20):
            """Checks an alias for uniqueness; if it is already taken, alter it
               (by append incrementing digits) until an available alias is found."""

            n = 1
            alias = in_str.lower()[:max_length]

            # keep on looping until an alias becomes available.
            # --
            # WARNING: this isn't going to work at high volumes, since the alias
            # that we return might be taken before we have time to do anything
            # with it! This should logic should probably be moved to the
            # initializer, to make the find/grab alias loop atomic
            while klass.objects.filter(alias__iexact=alias).count():
                alias = "%s%d" % (in_str.lower()[:max_length-len(str(n))], n)
                n += 1

            return alias

        # try each pattern, returning as
        # soon as we find something that fits
        for pat in patterns:
            m = re.match("^%s$" % pat, flat_name, re.IGNORECASE)
            if m is not None:
                g = m.groups()

                # return single names as-is
                # they might already be aliases
                if len(g) == 1:
                    alias = unique(g[0].lower())
                    return (alias, g[0], "")

                else:
                    # return only the letters from
                    # the first and last names
                    alias = unique(g[0][0] + re.sub(r"[^a-zA-Z]", "", g[1]))
                    return (alias.lower(), g[0], g[1])

        # we have no idea what is going on,
        # so just return the whole thing
        alias = unique(re.sub(r"[^a-zA-Z]", "", flat_name))
        return (alias.lower(), flat_name, "")

    class Meta:
        abstract = True        