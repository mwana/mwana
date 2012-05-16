SELECT district."name" as "District", locations_location."name" as "Clinic", extract( year from result_sent_date)::int "Year",
extract( week from result_sent_date)::int "Week",
'' as Command,
count(labresults_result.*)
FROM labresults_result
join locations_location on locations_location.id = labresults_result.clinic_id
join locations_location as district on district.id = locations_location.parent_id
where district."name" in ('Mazabuka','Monze')
group by "District","Clinic", "Year","Week"
order by 1,2,3,4;