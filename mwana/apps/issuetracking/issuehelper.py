# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.blacklist.models import BlacklistedPeople
from mwana.apps.training.models import Trained

from rapidsms.contrib.messagelog.models import Message
from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.issuetracking.models import Issue
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class IssueHelper:   
#    TODO take out generic methods here to a util/general 

    def get_paginated(self, query_set, page=1, num_pay_page=30):
        if not page:
            page = 1
        
            
        paginator = Paginator(query_set, num_pay_page)
        try:
            p_issues = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            p_issues = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            p_issues = paginator.page(paginator.num_pages)

#        counter = p_issues.start_index()
        
        number=p_issues.number
        has_previous = p_issues.has_previous()
        has_next = p_issues.has_next()
        paginator_num_pages = p_issues.paginator.num_pages
        return p_issues.object_list, paginator_num_pages, number, has_next, has_previous

    def get_issues(self, page=1):
        """
        Returns open issues with pagination
        """
        
        issues = Issue.objects.filter(open=True).order_by('pk')
        return self.get_paginated(issues, page, 30)

    def get_group_facilty_mappings(self, page=1):
        """
        Returns open group_facilty_mappings with pagination
        """

        issues = GroupFacilityMapping.objects.all().order_by('pk')
        return self.get_paginated(issues, page, 400)

    def get_group_user_mappings(self, page=1):
        """
        Returns open group_facilty_mappings with pagination
        """

        issues = GroupUserMapping.objects.all().order_by('pk')
        return self.get_paginated(issues, page, 400)

    def get_trained_people(self, order='pk', page=1):
        """
        Returns trained people
        """
        max_per_page = 400
        issues = Trained.objects.all().order_by(order)
        return self.get_paginated(issues, page, max_per_page), max_per_page

    def get_blacklisted_people(self, order='pk', page=1):
        """
        Returns blacklisted people
        """
        max_per_page = 400
        blacklist = (bl.phone for bl in BlacklistedPeople.objects.filter(valid=True))
        messages = Message.objects.filter(direction='I', connection__identity__in=blacklist).order_by('id')
        return self.get_paginated(messages, page, max_per_page), max_per_page
        
    
