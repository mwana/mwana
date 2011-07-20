SELECT case
when keyword = 'BIRTH' then 'MWANA'
else keyword
end as keyword,clinic,year(date) AS year, month(date) AS month
,count(*) 
--,*
FROM reports_messagegroup
WHERE keyword is NOT NULL AND direction='I'
AND before_pilot='f' 
AND backEND <> 'message tester'
and contact_type <> 'DBS Printer'


GROUP BY keyword,clinic,year, month
order by 1,2,3,4


