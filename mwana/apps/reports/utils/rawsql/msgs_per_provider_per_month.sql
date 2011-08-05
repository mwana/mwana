SELECT case
when rapidsms_backend.name= 'zain1'  then 'zain'
else rapidsms_backend.name
end as name

,year(date),month(date),direction,count(*)  from messagelog_message
--join reports_messagegroup on reports_messagegroup.id=messagelog_message.id
join rapidsms_connection on rapidsms_connection.id=messagelog_message.connection_id
join rapidsms_backend on rapidsms_backend.id=rapidsms_connection.backend_id
where rapidsms_backend.name<>'message_tester' 
--and year(date)=2011
--and month(date) between 4 and 6
group by year(date),month(date),rapidsms_backend.name,direction
order by year(date),month(date);


select * from rapidsms_backend