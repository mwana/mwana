DROP VIEW IF EXISTS labtests_viralloadview;
DROP TABLE IF EXISTS labtests_viralloadview;

CREATE OR REPLACE VIEW labtests_viralloadview
AS
select
labtests_result.id,
guspec,
requisition_id as ptid,
given_facility_name as original_facility,
nearest_facility_name,
collected_on as specimen_collection_date,
date_of_first_notification,
locations_location.name as facility_name,
district.name as district,
province.name as province,
locations_location.slug as facility_slug,
district.slug as district_slug,
province.slug as province_slug,
result,
test_type,
arrival_date as date_reached_moh,
result_sent_date as date_facility_retrieved_result,
rapidsms_contact.name as who_retrieved,
date_participant_notified as date_sms_sent_to_participant,
participant_informed as number_of_times_sms_sent_to_participant,
labtests_payload.source as data_source


   FROM labtests_result
   JOIN labtests_payload ON labtests_payload.id = labtests_result.payload_id
   LEFT JOIN locations_location ON locations_location.id = labtests_result.clinic_id
   LEFT JOIN locations_location district ON locations_location.parent_id = district.id
   LEFT JOIN locations_location province ON district.parent_id = province.id
   LEFT JOIN rapidsms_contact ON rapidsms_contact.id = labtests_result.who_retrieved_id;
