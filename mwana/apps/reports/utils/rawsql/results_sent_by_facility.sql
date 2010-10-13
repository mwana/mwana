SELECT province.name as province,district.name as district, clinic.name as clinic, count(*)
  FROM labresults_result
  LEFT JOIN locations_location clinic ON clinic.id=labresults_result.clinic_id
  LEFT JOIN locations_location district ON clinic.parent_id=district.id
  LEFT JOIN locations_location province ON district.parent_id=province.id

  WHERE entered_on>='2010-06-14'
  AND province.slug='luapula'
  and date(result_sent_date) between '2010-09-12' and '2010-10-12'

  GROUP BY province,district,clinic --ORDER BY province,district,clinic
   UNION ALL SELECT 'Total','Total','Total', (SELECT count(*) FROM labresults_result
   LEFT JOIN locations_location clinic ON clinic.id=labresults_result.clinic_id
  LEFT JOIN locations_location district ON clinic.parent_id=district.id
  LEFT JOIN locations_location province ON district.parent_id=province.id
  WHERE entered_on>='2010-06-14'
  AND province.slug='luapula'
  and date(result_sent_date) between '2010-09-12' and '2010-10-12')

   ORDER BY province,district,clinic
