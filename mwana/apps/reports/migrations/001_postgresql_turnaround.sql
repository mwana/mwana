DROP TABLE reports_turnaround;

CREATE VIEW reports_turnaround
AS
SELECT
     labresults_result.id,
     district.name as district,
     locations_location.name as facility,
     (entered_on-collected_on)+1 transporting,
     (processed_on-entered_on)+1 processing,
     (date(labresults_payload.incoming_date)-(processed_on)) +1 delays,
     (date(result_sent_date)-date(labresults_payload.incoming_date)) +1 retrieving,
     (date(result_sent_date)-collected_on)+1 turnaround,
     date(result_sent_date) date
FROM
     labresults_result join labresults_payload
     on labresults_payload.id=labresults_result.payload_id
     join locations_location on locations_location.id=labresults_result.clinic_id
     join locations_location as district on locations_location.parent_id=district.id
WHERE
     result IS NOT null
ORDER BY
     result_sent_date ASC
