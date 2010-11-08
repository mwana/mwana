from mwana import const


class LocationCode(object):

    def __init__(self, slug):
        self.slug = slug

    def __str__(self):
        return self.slug

    def __unicode__(self):
        return self.slug

    def get_worker_type(self):
        '''
        Returns the worker_type based on the location_code
        Expects code of format DDFF exactly.
        '''
        DD = self.slug[0:2]
        FF = self.slug[2:4]

        if FF == '00':
            return const.get_district_worker_type()
        else:
            return const.get_clinic_worker_type()

    def get_location_type(self):
        '''
        Returns the location_type_slug (district or clinic) based on the location_code
        Expects code of format DDFF exactly.
        '''
        DD = self.slug[0:2]
        FF = self.slug[2:4]

        if FF == '00':
            return const.DISTRICT_SLUGS
        else:
            return const.CLINIC_SLUGS
