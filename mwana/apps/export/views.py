# vim: ai ts=4 sts=4 et sw=4
# Create your views here.
import psycopg2
from mwana import localsettings as settings
from django.http import HttpResponse
import json
from mwana.apps.locations.models import Location
import sys
import logging
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

logger = logging.getLogger('mwana.apps.labresults.views')

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
        cursor.execute(SQL_QUERY_MEDIAN_CREATE_FUNC)
        cursor.execute(SQL_QUERY_SELECT)
        site_info_req = dictfetchall(cursor)

    except:
        log = "Error encountered when running query...", sys.exc_info()[1]
        logger.error(log)

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

SQL_QUERY_MEDIAN_CREATE_FUNC = '''
	CREATE OR REPLACE FUNCTION _final_median(NUMERIC[])
	   RETURNS NUMERIC AS
	$$
	   SELECT AVG(val)
	   FROM (
		 SELECT val
		 FROM unnest($1) val
		 ORDER BY 1
		 LIMIT  2 - MOD(array_upper($1, 1), 2)
		 OFFSET CEIL(array_upper($1, 1) / 2.0) - 1
	   ) sub;
	$$
	LANGUAGE 'sql' IMMUTABLE;

    DROP AGGREGATE IF EXISTS median(NUMERIC);

	CREATE AGGREGATE median(NUMERIC) (
	  SFUNC=array_append,
	  STYPE=NUMERIC[],
	  FINALFUNC=_final_median,
	  INITCOND='{}'
	);
'''

SQL_QUERY_SELECT = '''
--Level ID Key: 1:Facility, 2:District, 3:Province, 4:National

Select * from(
Select province,district,facility,x.facilityid,latitude,longitude,cast(x.turnaround as bigint) turnaround,result_month,result_year,rowd as totalsamples, 1 as levelID from (
		 Select FacilityId,result_month, result_year, median(turnaround) as turnaround, max(Rowdesc) rowd from (
		 Select *,
		   ROW_NUMBER() OVER (
		    PARTITION BY FacilityId,result_month, result_year
		    ORDER BY turnaround Asc) AS RowDesc
		    from (
		  SELECT
		       locations_location.slug as FacilityId,
		       (date(result_sent_date)-collected_on)+1 turnaround,
		       month(result_sent_date) result_month,
		       year(result_sent_date) result_year

		  FROM
		       labresults_result join labresults_payload
		       on labresults_payload.id=labresults_result.payload_id
		       join locations_location on locations_location.id=labresults_result.clinic_id
		  WHERE
		       notification_status = 'sent'
		       and result_sent_date >= '1/1/2014'
		  ORDER BY
		       result_sent_date ASC
		       ) u
		     ) q
		  GROUP BY FacilityId,result_month, result_year
		 ) x
		 left Join
		 (
		 SELECT
		      distinct (locations_location.slug) as FacilityId,
		      locations_location.name as Facility,
		      point.latitude Latitude,
		      point.longitude Longitude,
		      district.name as District,
		      province.name as Province
		 FROM
		      locations_location
		      left join locations_location as district on locations_location.parent_id=district.id
		      left join locations_location as province on district.parent_id = province.id
		      left join locations_point as point on locations_location.point_id = point.id
		 )y on x.facilityid = y.facilityid

union all
--district part
Select null as province,district,null as facility,null as facilityid,null as latitude,null as longitude,cast(median(turnaround) as bigint) turnaround,
result_month,result_year,max(RowDistrict) totalsamples, 2 as levelID
	from (
	Select *,
		ROW_NUMBER() OVER (
		    PARTITION BY district,result_month, result_year
		    ORDER BY turnaround Asc) AS RowDistrict
	 from (
	 --facility part
		Select province,district,facility,x.facilityid,latitude,longitude,cast(x.turnaround as bigint) turnaround,result_month,result_year,rowd as totalsamples from (
		 Select FacilityId,result_month, result_year, median(turnaround) as turnaround, max(Rowdesc) rowd from (
		 Select *,
		   ROW_NUMBER() OVER (
		    PARTITION BY FacilityId,result_month, result_year
		    ORDER BY turnaround Asc) AS RowDesc
		    from (
		  SELECT
		       locations_location.slug as FacilityId,
		       (date(result_sent_date)-collected_on)+1 turnaround,
		       month(result_sent_date) result_month,
		       year(result_sent_date) result_year

		  FROM
		       labresults_result join labresults_payload
		       on labresults_payload.id=labresults_result.payload_id
		       join locations_location on locations_location.id=labresults_result.clinic_id
		  WHERE
		       notification_status = 'sent'
		       and result_sent_date >= '1/1/2014'
		  ORDER BY
		       result_sent_date ASC
		       ) u
		     ) q
		  GROUP BY FacilityId,result_month, result_year
		 ) x
		 left Join
		 (
		 SELECT
		      distinct (locations_location.slug) as FacilityId,
		      locations_location.name as Facility,
		      point.latitude Latitude,
		      point.longitude Longitude,
		      district.name as District,
		      province.name as Province
		 FROM
		      locations_location
		      left join locations_location as district on locations_location.parent_id=district.id
		      left join locations_location as province on district.parent_id = province.id
		      left join locations_point as point on locations_location.point_id = point.id
		 )y on x.facilityid = y.facilityid
	--end facility part
	 ) j
) p GROUP BY district,result_month, result_year

union all
--province part
Select province,null as district,null as facility,null as facilityid,null as latitude,null as longitude,cast(median(turnaround) as bigint) turnaround,
result_month,result_year,max(RowDistrict) totalsamples, 3 as levelID
	from (
	Select *,
		ROW_NUMBER() OVER (
		    PARTITION BY province,result_month, result_year
		    ORDER BY turnaround Asc) AS RowDistrict
	 from (
	 --facility part
		Select province,district,facility,x.facilityid,latitude,longitude,cast(x.turnaround as bigint) turnaround,result_month,result_year,rowd as totalsamples from (
		 Select FacilityId,result_month, result_year, median(turnaround) as turnaround, max(Rowdesc) rowd from (
		 Select *,
		   ROW_NUMBER() OVER (
		    PARTITION BY FacilityId,result_month, result_year
		    ORDER BY turnaround Asc) AS RowDesc
		    from (
		  SELECT
		       locations_location.slug as FacilityId,
		       (date(result_sent_date)-collected_on)+1 turnaround,
		       month(result_sent_date) result_month,
		       year(result_sent_date) result_year

		  FROM
		       labresults_result join labresults_payload
		       on labresults_payload.id=labresults_result.payload_id
		       join locations_location on locations_location.id=labresults_result.clinic_id
		  WHERE
		       notification_status = 'sent'
		       and result_sent_date >= '1/1/2014'
		  ORDER BY
		       result_sent_date ASC
		       ) u
		     ) q
		  GROUP BY FacilityId,result_month, result_year
		 ) x
		 left Join
		 (
		 SELECT
		      distinct (locations_location.slug) as FacilityId,
		      locations_location.name as Facility,
		      point.latitude Latitude,
		      point.longitude Longitude,
		      district.name as District,
		      province.name as Province
		 FROM
		      locations_location
		      left join locations_location as district on locations_location.parent_id=district.id
		      left join locations_location as province on district.parent_id = province.id
		      left join locations_point as point on locations_location.point_id = point.id
		 )y on x.facilityid = y.facilityid
	--end facility part
	 ) j
) p GROUP BY province,result_month, result_year

union all
--National part
Select null as province,null as district,null as facility,null as facilityid,null as latitude,null as longitude,cast(x.turnaround as bigint) turnaround,
result_month,result_year,rowd as totalsamples, 4 as levelID from (
 Select result_month, result_year, median(turnaround) as turnaround, max(Rowdesc) rowd from (
 Select *,
   ROW_NUMBER() OVER (
    PARTITION BY result_month, result_year
    ORDER BY turnaround Asc) AS RowDesc
    from (
  SELECT
       (date(result_sent_date)-collected_on)+1 turnaround,
       month(result_sent_date) result_month,
       year(result_sent_date) result_year

  FROM
       labresults_result join labresults_payload
       on labresults_payload.id=labresults_result.payload_id
       join locations_location on locations_location.id=labresults_result.clinic_id
  WHERE
       notification_status = 'sent'
       and result_sent_date >= '1/1/2014'
  ORDER BY
       result_sent_date ASC
       ) u
     ) q
  GROUP BY result_month, result_year
 ) x
) z;
'''

