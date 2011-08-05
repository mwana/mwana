SELECT reports_messagegroup.clinic
--,contact_type
,phone_count total_phones
,phone
,count(*) usage
--,count(distinct phone) phones
 ,year(date) AS year

--,*
FROM reports_messagegroup
left join (select locations_location."name" clinic,
--"identity",
locations_location.id,
count(*) phone_count
from rapidsms_contact
join locations_location on locations_location.id=rapidsms_contact.location_id

join rapidsms_contact_types on rapidsms_contact_types.contact_id=rapidsms_contact.id
join contactsplus_contacttype on rapidsms_contact_types.contacttype_id=contactsplus_contacttype.id
join rapidsms_connection on rapidsms_connection.contact_id=rapidsms_contact.id
where type_id<>8
and "identity" like '+2609%'
group by locations_location."name",locations_location.id) as a
on a.clinic=reports_messagegroup.clinic
WHERE direction='I'
AND before_pilot='f' 
and year(date) = 2011
AND backEND <> 'message tester' 
AND contact_type not in ('DBS Printer','Community Based Agents')


GROUP BY reports_messagegroup.clinic,year,phone_count,phone--,contact_type
order by reports_messagegroup.clinic,usage desc,3,4

/*select * from reports_messagegroup
where contact_type is null
AND before_pilot='f' 
and year(date) = 2011
AND backEND <> 'message tester' 

*/