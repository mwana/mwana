SELECT DISTINCT
contactsplus_contacttype.slug,
CASE
WHEN locations_locationtype.sINgular ilike 'zone' then great_grANDy.name
WHEN locations_locationtype.sINgular ilike 'district' then parent.name
WHEN locations_locationtype.sINgular ilike 'provINce' then location.name
else grANDy."name"
END as provINce,
CASE
WHEN locations_locationtype.sINgular ilike 'zone' then grANDy.name
WHEN locations_locationtype.sINgular ilike 'district' then location.name
WHEN locations_locationtype.sINgular ilike 'provINce' then null
else parent."name"
END as district,
CASE
WHEN locations_locationtype.sINgular ilike 'zone' then parent.name
else location."name"
END as facility,
CASE
WHEN locations_locationtype.sINgular ilike 'zone' then location.name
else null
END as zone,
rapidsms_contact."name",
identity
FROM rapidsms_contact
LEFT JOIN rapidsms_connection ON rapidsms_connection.contact_id=rapidsms_contact.id
LEFT JOIN locations_location location ON rapidsms_contact.location_id=location.id
LEFT JOIN locations_location parent ON location.parent_id=parent.id
LEFT JOIN locations_location child ON child.parent_id=location.id
LEFT JOIN locations_location grANDy ON grANDy.id=parent.parent_id
LEFT JOIN locations_location great_grANDy ON great_grANDy.id=grANDy.parent_id
LEFT JOIN locations_locationtype ON locations_locationtype.id=location.type_id
LEFT JOIN rapidsms_contact_types ON rapidsms_contact_types.contact_id=rapidsms_contact.id
LEFT JOIN contactsplus_contacttype ON contactsplus_contacttype.id=rapidsms_contact_types.contacttype_id
WHERE is_active = 't'
AND rapidsms_connection.identity like '+260%'
AND location.name NOT ilike 'support'
--AND locations_locationtype.sINgular ilike 'zone'
ORDER BY 1,2,3,4

