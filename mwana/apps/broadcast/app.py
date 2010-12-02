# vim: ai ts=4 sts=4 et sw=4
import rapidsms

class App (rapidsms.apps.base.AppBase):
    
    def default(self, message):
        # No longer supporting BroadcastResponse, as per Merrick's email on the group:
        # http://groups.google.com/group/mwana/tree/browse_frm/thread/07f5d6599ac91832/695178783cf65e76
        pass
