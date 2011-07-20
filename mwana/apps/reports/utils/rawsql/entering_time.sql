SELECT round(sum(days)/count(days)::decimal) avg,sum(days) sum,count(days) count,"year","month"
FROM ( SELECT (arrival_date::date-processed_on::date) days,
 year(arrival_date) as "year", 
month(arrival_date) as "month",
slug
 from labresults_result
join locations_location on locations_location.id=clinic_id
where processed_on is not null and arrival_date::date between '2010-07-01' and '2011-04-15'
and processed_on <= arrival_date
and slug in ('402026','402030','402023','403011','403017','403029','403032','403012','406013','406015','406016','101027','102015','103014','202010','202013','208002','605014','605016','705002','706002'
)--,
--'808014','808030','808015','808025','808021','807099','807033','807026','807035','807037')
--order by "year","month"
) a
group by year,month
order by year,month