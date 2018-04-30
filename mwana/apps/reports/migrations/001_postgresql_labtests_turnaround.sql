DROP VIEW IF EXISTS reports_labteststurnaround;
DROP TABLE IF EXISTS reports_labteststurnaround;

CREATE OR REPLACE VIEW reports_labteststurnaround
AS
SELECT
     labtests_result.id,
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
     labtests_payload.source as lab
FROM
     labtests_result
     join locations_location on locations_location.id = labtests_result.clinic_id
     join locations_location as district on locations_location.parent_id = district.id
     join locations_location as province on district.parent_id = province.id
     join labtests_payload on labtests_payload.id = labtests_result.payload_id
WHERE
     result IS NOT null AND notification_status <> 'obsolete'
            and (collected_on <= processed_on or collected_on is null)
            and (entered_on <= processed_on or entered_on is null)
            and arrival_date >= processed_on
ORDER BY
     result_sent_date ASC;
