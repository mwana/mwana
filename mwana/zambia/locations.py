from mwana import const


class LocationCode(object):

    def __init__(self, slug):
        if len(slug) == 4:
            slug += '00' #pad with 00 for district code
        self.slug = slug

    def __str__(self):
        return self.slug

    def __unicode__(self):
        return self.slug

    def get_worker_type(self):
        '''
        Returns the worker_type based on the location_code
        Expects code of format PPDDFF exactly.
        '''
        PP = self.slug[0:2]
        DD = self.slug[2:4]
        FF = self.slug[4:6]

        if FF == '00':
            if DD == '00':
                return const.get_province_worker_type()
            else:
                return const.get_district_worker_type()
        else:
            return const.get_clinic_worker_type()

    def get_location_type(self):
        '''
        Returns the location_type_slug (Province, district or clinic) based on the location_code
        Expects code of format PPDDFF exactly.
        '''
        PP = self.slug[0:2]
        DD = self.slug[2:4]
        FF = self.slug[4:6]

        if FF == '00':
            if DD == '00':
                return const.PROVINCE_SLUGS
            else:
                return const.DISTRICT_SLUGS
        else:
            return const.CLINIC_SLUGS
