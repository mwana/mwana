DROP VIEW IF EXISTS reports_resultsforfollowup;
DROP TABLE IF EXISTS reports_resultsforfollowup;

CREATE OR REPLACE VIEW reports_resultsforfollowup
AS
SELECT
     labresults_result.id,
     province.name as province,
     district.name as district,
     locations_location.name as facility,
     sample_id as lab_id,
     requisition_id,
     birthdate,
     child_age,
     child_age_unit,
     sex,
     collected_on,
     entered_on as received_at_lab,
     processed_on,
     collecting_health_worker,
     verified,
     "result",
     date(arrival_date) date_reached_moh,
     date(result_sent_date) date_retrieved,
     labresults_payload.source as lab,
     clinic_id as facility_id,
     result_detail
FROM
     labresults_result
     join locations_location on locations_location.id = labresults_result.clinic_id
     join locations_location as district on locations_location.parent_id = district.id
     join locations_location as province on district.parent_id = province.id
     join labresults_payload on labresults_payload.id = labresults_result.payload_id
WHERE
     result IS NOT null 
     and result <> 'N'
            and collected_on <= processed_on
            and entered_on <= processed_on
            and arrival_date >= processed_on
ORDER BY
     result_sent_date ASC;
