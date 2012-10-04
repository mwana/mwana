SELECT distinct parent."name" as "District", clinic, --phone,
--rapidsms_contact.name,
year(messagelog_message.date ::date) as "Year",
(select extract (week from messagelog_message.date))::INTEGER  as "Week"
,'Confirm' as "Command"
,count (messagelog_message.text) as "Count"

from reports_messagegroup
join messagelog_message on messagelog_message.id=reports_messagegroup.id
--select messagelog_message.text,rapidsms_contact. * from messagelog_message
join rapidsms_contact on rapidsms_contact.id=messagelog_message.contact_id
join locations_location zones on zones.id = rapidsms_contact.location_id
join locations_location on locations_location.id = zones.parent_id
join locations_location parent on locations_location.parent_id = parent.id
join locations_location province on parent.parent_id= province.id
join rapidsms_contact_types on rapidsms_contact_types.contact_id = rapidsms_contact.id
join contactsplus_contacttype on contactsplus_contacttype.id = rapidsms_contact_types.contacttype_id

where 1=1--messagelog_message.direction = 'I'
and messagelog_message.date >= '2011-07-1' and messagelog_message.date < '2012-05-01'
AND backEND <> 'message tester'
and parent."name" in ('Mazabuka','Monze')
and (messagelog_message.text ilike 'confirm%' or messagelog_message.text ilike 'comfirm%')
--and parent.slug like '80%'

group by parent."name",clinic, "Year","Week"--, contactsplus_contacttype.slug--, phone
order by 1,2,3,4;
