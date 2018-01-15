# vim: ai ts=4 sts=4 et sw=4

CHW_MESSAGE = "Hello %(name)s. %(client)s is due for %(visit_type)s on %(date)s."
M8 = '''Happy day!
oooO
(....).... Oooo....
.\\..(.....(.....)...
. .\\_)..... )../....
. ......... (_/.....
%(date)s'''
M9 = '''
&&&&&&&
 && & &&
      ) (
      ! !
      ) (
%(date)s'''

CLIENT_MESSAGE_CHOICES = {'m1': 'Happy health day %(date)s',
                   'm2': 'Good day. Happy day %(date)s',
                   'm3': 'Time up %(date)s',
                   'm4': 'One Zambia one nation. %(date)s',
                   'm5': 'Thank you %(date)s',
                   'm6': 'Remember %(date)s',
                   'm7': None, #'Did you know? On %(date)s %(fact)s',
                   'm8': M8,
                   'm9': M9}