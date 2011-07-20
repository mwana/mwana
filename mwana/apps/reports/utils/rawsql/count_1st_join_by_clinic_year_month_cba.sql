 SELECT keyword,
--text,
case 
when clinic is null then clinic(text)
else clinic
end as clinic
,year(date) AS year, month(date) AS month
,count(*) count
--,*
FROM reports_messagegroup
WHERE (keyword='CBA' or keyword='AGENT' or (keyword ='JOIN' and text ilike '%cba%')) 
AND direction='I'

--AND before_pilot='f' 
AND backEND <> 'message tester' 
and clinic is null
and phone like '+2609%'
and phone not in (select phone
from reports_messagegroup
where direction = 'I'
group by phone
having count(distinct clinic)>1)

GROUP BY keyword,clinic,year, month,clinic(text)--,text
order by clinic,year,month

