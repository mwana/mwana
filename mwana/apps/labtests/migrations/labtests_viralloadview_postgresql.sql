DROP VIEW IF EXISTS labtests_viralloadview;
DROP TABLE IF EXISTS labtests_viralloadview;

CREATE OR REPLACE VIEW labtests_viralloadview
AS
select
labtests_result.id,
guspec,
collected_on as specimen_collection_date,
locations_location.name as facility_name,
result,
arrival_date as date_reached_moh,
result_sent_date as date_facility_retrieved_result,
rapidsms_contact.name as who_retrieved,
date_participant_notified as date_sms_sent_to_participant,
participant_informed as number_of_times_sms_sent_to_participant,
labtests_payload.source as data_source


FROM labtests_result
labtests_result join labtests_payload
     on labtests_payload.id=labtests_result.payload_id
    LEFT join locations_location on locations_location.id=labtests_result.clinic_id
    LEFT JOIN rapidsms_contact on rapidsms_contact.id=labtests_result.who_retrieved_id
