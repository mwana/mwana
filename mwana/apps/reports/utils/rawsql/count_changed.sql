SELECT name clinic,old_value as "old_id:result",requisition_id new_id,"result" new_result, result_sent_date FROM labresults_result
join locations_location on clinic_id=locations_location.id
where record_change is not null
order by name
