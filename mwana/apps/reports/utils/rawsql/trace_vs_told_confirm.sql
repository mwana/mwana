SELECT clinic,year,month,sum(birth) births, sum(told) told, sum(confirm) confirm from (
SELECT 0 as birth, 1 as told, 0 as confirm,
case 
when clinic is null then clinic(text)
else clinic
end as clinic
,year(date) AS year, month(date) AS month
,1 count
FROM reports_messagegroup
WHERE keyword = 'TOLD' AND direction='I'

AND before_pilot='f' 
AND backEND <> 'message tester' 
and contact_type <> 'DBS Printer'

and phone like '+2609%'
and phone not in (select phone
from reports_messagegroup
where direction = 'I'
group by phone
having count(distinct clinic)>1)

union all

SELECT 0 as birth, 0 as told, 1 as confirm,
case 
when clinic is null then clinic(text)
else clinic
end as clinic
,year(date) AS year, month(date) AS month
,1 count
FROM reports_messagegroup
WHERE keyword ='CONFIRM' AND direction='I'

AND before_pilot='f' 
AND backEND <> 'message tester' 
and contact_type <> 'DBS Printer'

and phone like '+2609%'
and phone not in (select phone
from reports_messagegroup
where direction = 'I'
group by phone
having count(distinct clinic)>1)

union all


select 1 births, 0 as told, 0 as confirm, clinic."name" clinic,
year(reminders_patientevent."date_logged") as year,
month(reminders_patientevent."date_logged") as month,
1 as count from reminders_patientevent
join rapidsms_contact on rapidsms_contact.id=patient_id
join locations_location on locations_location.id=rapidsms_contact.location_id
join locations_location clinic on clinic.id=locations_location.parent_id
) a
group by clinic,year,month
order by clinic,year,month