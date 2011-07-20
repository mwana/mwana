SELECT  location,name,phone,count(*)
--,year(date) as year
--,month(date) as month
,date::date as date from noretries
--where phone= '+260977853658'
group by name
--,year
--, month
,phone
,location
,date
order by date,location,name,phone,count