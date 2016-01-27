# vim: ai ts=4 sts=4 et sw=4
# Create your views here.
import psycopg2
from mwana import localsettings as settings
from django.http import HttpResponse
import json
from mwana.apps.locations.models import Location
from collections import OrderedDict


def get_turnaround(request):
    '''
    key_value = ""
    if ((request.method == 'GET') and ('key_value' in request.GET)):
        key_value = request.GET['key_value']
    '''
    connection = psycopg2.connect(host=settings.DATABASES['default']['HOST'], database=settings.DATABASES['default']['NAME'],\
                    user=settings.DATABASES['default']['USER'], password=settings.DATABASES['default']['PASSWORD'])
    
    districts = Location.objects.filter().distinct()
    
    site_info_req = OrderedDict()

    try:
        cursor = connection.cursor()
        cursor.execute(SQL_QUERY_SELECT) 
        site_info_req = dictfetchall(cursor)

    except:
        log = "oops...", sys.exc_info()
    finally:
        connection.close()
        return HttpResponse(json.dumps(site_info_req))   

def dictfetchall(cursor):
    # "Returns all rows from a cursor as a dict"
    to_return_dict = []
    desc = cursor.description
    if cursor.rowcount > 0:
        o_dict_rows = [
            OrderedDict(zip([str(col[0]) for col in desc], row))
            for row in cursor.fetchall()
        ]

        for row in o_dict_rows:
            o_dict_str = OrderedDict()
            for key,val in row.items():
                o_dict_str[key] = str(val)

            to_return_dict.append(o_dict_str)
    else:
        cols = [desc[0] for desc in cursor.description]
        dict_cols = OrderedDict()
        for col in cols:
            dict_cols[col] = ''
        to_return_dict.append(dict_cols)

    return to_return_dict

SQL_QUERY_SELECT = '''
    Select x.province,x.district,x.facility,x.facilityid,x.latitude,x.longitude,x.turnaround,x.result_month,x.result_year,y.rowd as totalsamples from 
	(
		Select *,	
			ROW_NUMBER() OVER (
			 PARTITION BY FacilityId,result_month, result_year
			 ORDER BY turnaround Desc) AS RowDesc 
			 from (
		SELECT
		     province.name as Province,
		     district.name as District,
		     locations_location.name as Facility,
		     locations_location.slug as FacilityId,
		     point.latitude Latitude,
		     point.longitude Longitude,
		     (date(result_sent_date)-collected_on)+1 turnaround,
		     month(result_sent_date) result_month,
		     year(result_sent_date) result_year
		     
		FROM
		     labresults_result join labresults_payload
		     on labresults_payload.id=labresults_result.payload_id
		     join locations_location on locations_location.id=labresults_result.clinic_id
		     left join locations_location as district on locations_location.parent_id=district.id
		     left join locations_location as province on district.parent_id = province.id
		     left join locations_point as point on locations_location.point_id = point.id
		WHERE
		     notification_status = 'sent'
		     and result_sent_date >= '1/1/2014'
		ORDER BY
		     result_sent_date ASC
		     ) u
	) x
    join (
	select *,(case when rowd%2 = 1 then (rowd/2) + 1 else rowd/2 end) as midPoint from (
		select facilityid, result_month, result_year, max(RowDesc) rowd 
		from 
		(
			Select *,	
				ROW_NUMBER() OVER (
				 PARTITION BY FacilityId,result_month, result_year
				 ORDER BY turnaround Desc) AS RowDesc 
				 from (
			SELECT
			     district.name as District,
			     locations_location.name as Facility,
			     locations_location.slug as FacilityId,
			     (date(result_sent_date)-collected_on)+1 turnaround,
			     month(result_sent_date) result_month,
			     year(result_sent_date) result_year
			     
			FROM
			     labresults_result join labresults_payload
			     on labresults_payload.id=labresults_result.payload_id
			     join locations_location on locations_location.id=labresults_result.clinic_id
			     left join locations_location as district on locations_location.parent_id=district.id
			WHERE
			     notification_status = 'sent'
			     and result_sent_date >= '1/1/2014'
			ORDER BY
			     result_sent_date ASC
			     ) u
		) k
		group by facilityid,result_month,result_year
	) b order by result_month,result_year
    ) y on x.facilityid = y.facilityid and x.result_month=y.result_month and x.result_year=y.result_year and x.rowdesc=y.midpoint
    order by x.facilityid
'''





