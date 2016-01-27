# vim: ai ts=4 sts=4 et sw=4
from rapidsms.tests.scripted import TestScript

class TestApp(TestScript):
    
    def testSQL(self):
        SQL_QUERY_SELECT = '''
                Select x.district,x.facility,x.facilityid,x.turnaround,x.result_month,x.result_year,y.rowd as totalsamples from 
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
		                 join locations_location as district on locations_location.parent_id=district.id
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
			                 join locations_location as district on locations_location.parent_id=district.id
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
