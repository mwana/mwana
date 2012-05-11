SELECT parent."name" as "District", locations_location."name" as "Facility", min(result_sent_date)::date as "Date Of First Results" from labresults_result
join locations_location on locations_location.id=labresults_result.clinic_id
join locations_location parent on parent.id = locations_location.parent_id
where parent."name" in ('Mazabuka','Monze')

group by parent."name", locations_location."name"
order by parent."name", locations_location."name"