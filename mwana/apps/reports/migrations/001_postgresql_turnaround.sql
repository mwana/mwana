DROP VIEW reports_turnaround;
DROP TABLE reports_turnaround;

CREATE VIEW reports_turnaround
AS
SELECT
     labresults_result.id,
     district.name as district,
     locations_location.name as facility,
     (entered_on-collected_on)+1 transporting,
     (processed_on-entered_on)+1 processing,
     (date(arrival_date)-(processed_on)) +1 delays,
     (date(result_sent_date)-date(arrival_date)) +1 retrieving,
     (date(result_sent_date)-collected_on)+1 turnaround,
     arrival_date date_reached_moh,
     date(result_sent_date) date_retrieved
FROM
     labresults_result
     join locations_location on locations_location.id=labresults_result.clinic_id
     join locations_location as district on locations_location.parent_id=district.id
WHERE
     result IS NOT null
ORDER BY
     result_sent_date ASC
