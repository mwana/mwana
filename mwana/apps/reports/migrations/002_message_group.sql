drop view reports_messagegroup;
drop table reports_messagegroup;


create view reports_messagegroup
as
SELECT messagelog_message.id, rapidsms_connection.identity  as
 phone,
CASE
WHEN backEND_id= 1 then 'pygsm'
WHEN backEND_id= 2 then 'message tester'
END
::varchar(15) as backEND , direction, date, "text",
CASE
WHEN trim(text) ilike 'join%' then 'JOIN'
WHEN trim(text) ilike 'agent%' then 'AGENT'
WHEN trim(text) ilike 'birth%' then 'BIRTH'
WHEN trim(text) ilike 'mwana%' then 'MWANA'
WHEN trim(text) ilike 'cba%' then 'CBA'
WHEN trim(text) ilike 'all%' then 'ALL'
WHEN trim(text) ilike 'clinic%' then 'CLINIC'
WHEN trim(text) ilike 'invalid%' then 'INVALID'
WHEN trim(text) ilike '% to all]' then 'TO ALL'
WHEN trim(text) ilike '% to cba]' then 'TO CBA'
WHEN trim(text) ilike '% to clinic]' then 'TO CLINIC'
WHEN trim(text) ilike '%Please make sure your code is a 4-digit number like 1234%' then 'BAD CODE'
END

::varchar(15) as keyword,
CASE
WHEN trim(text) ilike 'Make a followup for changed results%' then true
WHEN trim(text) ilike 'URGENT:%' then true
else false
END
as changed_res,
CASE
WHEN trim(text) ilike '%test results ready for you. Please reply to%' then true
else false
END
::boolean  as new_results,

 ''::varchar(10)  as app,contactsplus_contacttype.name as contact_type,
 CASE
 WHEN locations_locationtype.slug='zone' then parentlocation.name
 else mylocation.name
 END as clinic

  FROM messagelog_message
  LEFT JOIN rapidsms_connection ON rapidsms_connection.id=messagelog_message.connection_id
  LEFT JOIN rapidsms_contact ON rapidsms_contact.id=messagelog_message.contact_id
  LEFT JOIN rapidsms_contact_types ON rapidsms_contact_types.contact_id=messagelog_message.contact_id
  LEFT JOIN contactsplus_contacttype ON contactsplus_contacttype.id=rapidsms_contact_types.contacttype_id
  LEFT JOIN locations_location mylocation ON mylocation.id=rapidsms_contact.location_id
  LEFT JOIN locations_location parentlocation ON parentlocation.id=mylocation.parent_id
  LEFT JOIN locations_locationtype ON locations_locationtype.id = mylocation.type_id
;