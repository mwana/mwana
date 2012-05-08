SELECT distinct district."name", clinic, contactsplus_contacttype."slug",--phone,
min(messagelog_message.date):: date as "Date of First SMS"
from reports_messagegroup
join messagelog_message on messagelog_message.id=reports_messagegroup.id
--select messagelog_message.text,rapidsms_contact. * from messagelog_message
join rapidsms_contact on rapidsms_contact.id=messagelog_message.contact_id
join locations_location on locations_location.id = rapidsms_contact.location_id
join locations_location parent on locations_location.parent_id = parent.id
join locations_location district on parent.parent_id= district.id
join rapidsms_contact_types on rapidsms_contact_types.contact_id = rapidsms_contact.id
join contactsplus_contacttype on contactsplus_contacttype.id = rapidsms_contact_types.contacttype_id

where 1=1--messagelog_message.direction = 'I'
--and messagelog_message.date > '2010-12-13'
AND backEND <> 'message tester'
and is_active = true
and district."name" in ('Mazabuka','Monze')
--and parent.slug like '80%'

group by district."name",clinic, contactsplus_contacttype.slug--, phone
order by 1,2
