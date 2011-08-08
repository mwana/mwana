select distinct clinic.name as facility, reminders_appointment.name as visit,
--count(distinct patient_id),
patient_id
--recipient_id--,reminders_sentnotification.*, reminders_patientevent.*
from reminders_sentnotification
join reminders_patientevent on reminders_sentnotification.patient_event_id=reminders_patientevent.id
join reminders_event on reminders_event.id=reminders_patientevent.event_id
join reminders_appointment on reminders_appointment.event_id=reminders_event.id
join rapidsms_contact on rapidsms_contact.id=patient_id
join locations_location zone on zone.id=rapidsms_contact.location_id
join locations_location clinic on clinic.id=zone.parent_id
where reminders_sentnotification.date_logged between '20110101' and '20110201'
--group by facility,visit,recipient_id
order by 1,2
