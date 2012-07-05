#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class AddIssuetHandler(KeywordHandler):
    """
    """

    keyword = "add issue|create issue|issue add|issue create|add isue|create isue|isue add|isue create"
   

    HELP_TEXT = "To add an issue send ADD ISSUE [Description]"
        
    def help(self):
        self.respond(self.HELP_TEXT)    

    def handle(self, text):
        pass