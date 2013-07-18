# vim: ai ts=4 sts=4 et sw=4

from django.contrib.auth.models import User
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from mwana.apps.locations.models import Location
from mwana.apps.reports.webreports.models import ReportingGroup

class WebUserService:
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



        number = p_issues.number
        has_previous = p_issues.has_previous()
        has_next = p_issues.has_next()
        paginator_num_pages = p_issues.paginator.num_pages
        return p_issues.object_list, paginator_num_pages, number, has_next, has_previous, num_pay_page

    def user_facilities_count(self, user):
        user_groups = ReportingGroup.objects.filter(groupusermapping__user=
                                                    user).distinct()
        
        return Location.objects.filter(groupfacilitymapping__group__in=
                                user_groups).distinct().count()

    def get_web_users(self, current_user, page=1, group=None, district=None, province=None):
        to_return = []
        user_groups = ReportingGroup.objects.filter(groupusermapping__user=
                                                    current_user).distinct()
        if group and group.lower().strip() != 'all':
            user_groups = [group]
        
        peers = User.objects.filter(is_active=True, groupusermapping__group__in=user_groups).distinct()

        for peer in peers:
            to_return.append(peer)


        user_facilities = Location.objects.filter(
                                                  groupfacilitymapping__group__in=
                                                  user_groups).distinct()



        if district and district.lower().strip() != 'all':
            user_facilities = user_facilities.filter(parent__slug=district)
        elif province and province.lower().strip() != 'all':
            user_facilities = user_facilities.filter(parent__parent__slug=province)

        my_facilities_count = len(user_facilities.distinct())
        
        if my_facilities_count == 0:
            return self.get_paginated(list(set(to_return)), page, 30)


        other_users = User.objects.filter(is_active=True, groupusermapping__group__groupfacilitymapping__facility__in
                                          =user_facilities).exclude(
                                          id=current_user.id).distinct()
        for user in other_users:
            if self.user_facilities_count(user) and my_facilities_count >= self.user_facilities_count(user):
                to_return.append(user)

        
        return self.get_paginated(list(set(to_return)), page, 30)

