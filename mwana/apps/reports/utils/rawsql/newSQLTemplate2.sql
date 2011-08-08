select count( distinct messagelog_message.connection_id) from messagelog_message
where text ilike 'join%'
and date > '2010-12-31'
and contact_id is null
--order by date

select * from rapidsms_connection
where "identity" is null


select * from messagelog_message
join rapidsms_contact on rapidsms_contact.id=messagelog_message.contact_id
where connection_id is null
and direction = 'I'
and date > '2010-06-13'