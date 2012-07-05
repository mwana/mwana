SELECT rapidsms_backend."name", rapidsms_connection."identity", messagelog_message."date", messagelog_message.direction FROM messagelog_message
join rapidsms_connection on rapidsms_connection.id =  messagelog_message.connection_id
join rapidsms_backend on rapidsms_backend.id=rapidsms_connection.backend_id
where rapidsms_backend."name"='zain-smpp'
order by "date"
