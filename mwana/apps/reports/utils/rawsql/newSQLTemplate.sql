
SELECT parent."name" as "District", locations_location."name" as "Clinic",
 rapidsms_contact."name", contactsplus_contacttype."name" ,
rapidsms_connection."identity" as "Phone",messagelog_message.direction, messagelog_message.date, text  from messagelog_message
join rapidsms_contact on rapidsms_contact.id = messagelog_message.contact_id
join locations_location on locations_location.id = rapidsms_contact.location_id
join rapidsms_connection on rapidsms_connection.id = messagelog_message.connection_id
--select * FROM locations_location
left join locations_location as parent on parent.id = locations_location.parent_id
join rapidsms_contact_types on rapidsms_contact_types.contact_id = rapidsms_contact.id
join contactsplus_contacttype on contactsplus_contacttype.id = rapidsms_contact_types.contacttype_id
--where parent.slug in ('808030', '808014', '808021', '808015', '808025', '807035', '807026', '807033', '807037', '807099', '804011', '804012', '804013', '804001', '804031', '804028', '804022', '804034', '804016', '804002', '804030', '804024')
where locations_location.slug in ('800000', '800000', '800000')--, '808015', '808025', '807035', '807026', '807033', '807037', '807099', '804011', '804012', '804013', '804001', '804031', '804028', '804022', '804034', '804016', '804002', '804030', '804024')
--and messagelog_message.direction ='I'
and messagelog_message.date between '20110101' and '20121001'
order by 1,2,3,"Phone", date

--SELECT * from contactsplus_contacttype

