SELECT district as "District", locations_location.name as "Facility", facility_slug as "Code", median(transporting)::int as "Transport Time", median(processing)::int as "Processing Time"
, median(delays)::int as "Date entry & delays" , median(retrieving)::int as "Retrieving Time", median(turnaround)::int as "Turnaround"  from locations_location
LEFT JOIN reports_turnaround tn on tn.facility_id = locations_location.id
where locations_location.slug in ('813004', '813001', '813007', '813002', '813011', '813012',
                  '813015', '813014', '801010', '801099', '801038', '801002', '801002', '801019',
                  '801020', '801022', '801039', '801028', '801035', '802099', '804030', '804014',
                  '804034', '804013', '804046', '805010', '805012', '805013', '805026', '805025',
                  '805022', '806019', '806011', '806022', '806003', '806007', '806012', '806013',
                  '806018', '806008', '806010', '806016', '806002', '806025', '806026', '805029',
                  '806010hp', '806017', '806021', '807014', '807048', '807015', '807016',
                  '807017', '807019', '807021', '807021', '807022', '807023', '807024', '807025',
                  '807026', '807027', '807030', '807029', '807055', '807033', '807036', '807037',
                  '807032', '807049', '807038', '807041', '807001', '808016', '808022', '808025',
                  '808014', '808030', '808011', '808013', '808001', '811013', '811001', '804012',
                  '804031', '801016', '801025', '801026')

                  group by district, locations_location.name, facility_slug
                  order by district, locations_location.name, facility_slug;
                  