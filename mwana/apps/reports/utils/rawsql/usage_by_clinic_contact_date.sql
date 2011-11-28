SELECT clinic,messagelog_message.text, phone,rapidsms_contact."name",messagelog_message.date from reports_messagegroup
join messagelog_message on messagelog_message.id=reports_messagegroup.id
--select messagelog_message.text,rapidsms_contact. * from messagelog_message
join rapidsms_contact on rapidsms_contact.id=messagelog_message.contact_id
join locations_location on locations_location.id = rapidsms_contact.location_id
join locations_location parent on locations_location.parent_id = parent.id

where messagelog_message.direction = 'I'
and messagelog_message.date > '2010-06-13'
and parent.slug like '8080%'
AND backEND <> 'message tester'
and is_active = true

order by clinic, phone, text