SELECT count (distinct reminders_sentnotification.patient_event_id), reminders_appointment."name" as type, district.name district from reminders_sentnotification
join reminders_patientevent on reminders_patientevent.id = reminders_sentnotification.patient_event_id
join reminders_appointment on reminders_appointment.id= reminders_sentnotification.appointment_id

left join rapidsms_contact on rapidsms_contact.id=reminders_patientevent.patient_id
left join locations_location as zone on zone.id=rapidsms_contact.location_id
left join locations_location as clinic on zone.parent_id =clinic.id
left join locations_location as district on clinic.parent_id =district.id
--where --district.slug like '80%'
--and reminders_patientevent.date_logged > '2011-10-10'
group by district.name, reminders_appointment."name"
order by district.name, reminders_appointment."name";

