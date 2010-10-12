SELECT province,district,facility,round((sum(turnarround)+0.1)/count(*)) as turnaround
FROM
(
SELECT
province.name as province,
     district.name as District,
     locations_location.name as Facility,
     (date(result_sent_date)-collected_on)+1 turnarround

FROM
     labresults_result join labresults_payload
     ON labresults_payload.id=labresults_result.payload_id
     join locations_location ON locations_location.id=labresults_result.clinic_id
     join locations_location as district ON locations_location.parent_id=district.id
     LEFT JOIN locations_location province ON district.parent_id=province.id
WHERE
     notification_status = 'sent'
     AND entered_on>='2010-06-14'
     AND province.slug='luapula' ) a
      GROUP BY
province,district,facility
 ORDER BY
province,district,facility