DROP VIEW IF EXISTS reports_turnaround;
DROP TABLE IF EXISTS reports_turnaround;

CREATE OR REPLACE VIEW reports_turnaround
AS
SELECT
     labresults_result.id,
     labresults_result.sample_id,
     labresults_result.requisition_id,
     labresults_result.result,
     province.name as Province,
     district.name as district,
     locations_location.name as facility,
     locations_location.id as facility_id,
     locations_location.slug as facility_slug,
     (entered_on-collected_on) + 1 transporting,
     (processed_on-entered_on) + 1 processing,
     (date(arrival_date) - (processed_on)) + 1 delays,
     (date(result_sent_date) - date(arrival_date)) +1 retrieving,
     (date(result_sent_date) - collected_on) + 1 turnaround,
     collected_on,
     entered_on as received_at_lab,
     processed_on,
     date(arrival_date) date_reached_moh,
     date(result_sent_date) date_retrieved,
     labresults_payload.source as lab
FROM
     labresults_result
     join locations_location on locations_location.id = labresults_result.clinic_id
     join locations_location as district on locations_location.parent_id = district.id
     join locations_location as province on district.parent_id = province.id
     join labresults_payload on labresults_payload.id = labresults_result.payload_id
WHERE
     result IS NOT null AND notification_status <> 'obsolete'
            and (collected_on <= processed_on or collected_on is null)
            and (entered_on <= processed_on or entered_on is null)
            and arrival_date >= processed_on
ORDER BY
     result_sent_date ASC;
