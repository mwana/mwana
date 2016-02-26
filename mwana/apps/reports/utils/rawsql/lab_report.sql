select name as district,
source as lab,
COALESCE(sum(rejected),0) + COALESCE(sum(positive),0) + COALESCE(sum(negative),0)+ COALESCE(sum(pending_testing),0) as total_received_at_lab,
COALESCE(sum(rejected),0) + COALESCE(sum(positive),0) + COALESCE(sum(negative),0) as number_processed,
 sum(pending_testing) as pending_processing,
 sum(rejected) as rejected, sum(positive) as positive, sum(negative) as negative, sum(retrieved) as retrieved
from
(
select count(labresults_result.id) as retrieved, 0 as rejected, 0 as positive, 0 as negative, 0 as pending_testing, labresults_payload.source,  district.name from labresults_result
join labresults_payload on labresults_payload.id = labresults_result.payload_id
join locations_location clinic on clinic.id = clinic_id
join locations_location district on district.id = clinic.parent_id
join locations_location province on province.id = district.parent_id
where entered_on between '2015-06-01' and '2015-06-30'
and province.name = 'Southern'
and (notification_status = 'sent' or (notification_status = 'obsolete' and result_sent_date > '2015-05-31') )
group by labresults_payload.source,  district.name


union all
select 0 as retrieved, count(labresults_result.id) as rejected, 0 as positive, 0 as negative, 0 as pending_testing, labresults_payload.source,  district.name from labresults_result
join labresults_payload on labresults_payload.id = labresults_result.payload_id
join locations_location clinic on clinic.id = clinic_id
join locations_location district on district.id = clinic.parent_id
join locations_location province on province.id = district.parent_id
where entered_on between '2015-06-01' and '2015-06-30'
and province.name = 'Southern'
and result in ('I', 'R', 'X')
group by labresults_payload.source,  district.name


union all
select 0 as retrieved, null as  rejected, count(labresults_result.id) as positive, null as negative, null as pending_testing, labresults_payload.source,  district.name from labresults_result
join labresults_payload on labresults_payload.id = labresults_result.payload_id
join locations_location clinic on clinic.id = clinic_id
join locations_location district on district.id = clinic.parent_id
join locations_location province on province.id = district.parent_id
where entered_on between '2015-06-01' and '2015-06-30'
and province.name = 'Southern'
and result = 'P'
group by labresults_payload.source,  district.name

union all
select 0 as retrieved, null as  rejected, null as positive, count(labresults_result.id) as negative, null as pending_testing, labresults_payload.source,  district.name from labresults_result
join labresults_payload on labresults_payload.id = labresults_result.payload_id
join locations_location clinic on clinic.id = clinic_id
join locations_location district on district.id = clinic.parent_id
join locations_location province on province.id = district.parent_id
where entered_on between '2015-06-01' and '2015-06-30'
and province.name = 'Southern'
and result = 'N'
group by labresults_payload.source,  district.name

union all
select 0 as retrieved, null as  rejected, null as positive, 0 as negative, count(labresults_result.id) as pending_testing, labresults_payload.source,  district.name from labresults_result
join labresults_payload on labresults_payload.id = labresults_result.payload_id
join locations_location clinic on clinic.id = clinic_id
join locations_location district on district.id = clinic.parent_id
join locations_location province on province.id = district.parent_id
where entered_on between '2015-06-01' and '2015-06-30'
and province.name = 'Southern'
and result in ('', null)
group by labresults_payload.source,  district.name

) data

group by source, name
order by name, source
