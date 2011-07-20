select * from (SELECT clinic,year,month,sum(trace) trace, sum(told) told, sum(confirm) confirm from (
SELECT 0 as trace, 1 as told, 0 as confirm,
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

SELECT 0 as trace, 0 as told, 1 as confirm,
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

SELECT 1 as trace, 0 as told, 0 as confirm,
case 
when clinic is null then clinic(text)
else clinic
end as clinic
,year(date) AS year, month(date) AS month
,1 count
FROM reports_messagegroup
WHERE keyword ='TRACE' AND direction='I'

AND before_pilot='f' 
AND backEND <> 'message tester' 
and contact_type <> 'DBS Printer'

and phone like '+2609%'
and phone not in (select phone
from reports_messagegroup
where direction = 'I'
group by phone
having count(distinct clinic)>1)


) a
group by clinic,year,month) b
where trace>0
order by clinic,year,month