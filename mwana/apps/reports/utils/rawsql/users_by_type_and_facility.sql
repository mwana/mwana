SELECT contactsplus_contacttype.name,count(*) from rapidsms_contact
LEFT JOIN rapidsms_contact_types ON rapidsms_contact_types.contact_id=rapidsms_contact.id
LEFT JOIN contactsplus_contacttype ON contactsplus_contacttype.id=rapidsms_contact_types.contacttype_id
LEFT JOIN rapidsms_connection ON rapidsms_connection.contact_id=rapidsms_contact.id
LEFT JOIN locations_location location ON rapidsms_contact.location_id=location.id
LEFT JOIN locations_location parent ON location.parent_id=parent.id
WHERE is_active='t'
and contactsplus_contacttype.name <> 'Patient'
AND rapidsms_connection.identity like '+260%'
and (location.slug like '80%' or parent.slug like '80%')
group by contactsplus_contacttype.name

