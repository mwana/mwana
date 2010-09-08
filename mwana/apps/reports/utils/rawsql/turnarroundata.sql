SELECT
     district.name,
     locations_location.name,
     (entered_on-collected_on)+1 transport,
     (processed_on-entered_on)+1 testing,
     (date(labresults_payload.incoming_date)-(processed_on)) +1 staging,
     (date(result_sent_date)-date(labresults_payload.incoming_date)) +1 retrieving,
     (date(result_sent_date)-collected_on)+1 turnarround,
     date(result_sent_date) date
FROM
     labresults_result join labresults_payload
     on labresults_payload.id=labresults_result.payload_id
     join locations_location on locations_location.id=labresults_result.clinic_id
     join locations_location as district on locations_location.parent_id=district.id
WHERE
     notification_status = 'sent'
ORDER BY
     result_sent_date ASC