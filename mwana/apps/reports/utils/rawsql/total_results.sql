SELECT 'After pilot' as Afterpilot, (SELECT count(*) FROM labresults_result
   LEFT JOIN locations_location clinic ON clinic.id=labresults_result.clinic_id
  LEFT JOIN locations_location district ON clinic.parent_id=district.id
  LEFT JOIN locations_location province ON district.parent_id=province.id
  WHERE entered_on>='2010-06-14'
and date(result_sent_date) between '2010-09-12' and '2010-10-12'
  AND province.slug='luapula') count

  union all
  SELECT 'Before pilot'  , (SELECT count(*) FROM labresults_result
   LEFT JOIN locations_location clinic ON clinic.id=labresults_result.clinic_id
  LEFT JOIN locations_location district ON clinic.parent_id=district.id
  LEFT JOIN locations_location province ON district.parent_id=province.id
  WHERE entered_on<'2010-06-14'
and date(result_sent_date) between '2010-09-12' and '2010-10-12'
  AND province.slug='luapula')
   union all
  SELECT 'Total'  , (SELECT count(*) FROM labresults_result
   LEFT JOIN locations_location clinic ON clinic.id=labresults_result.clinic_id
  LEFT JOIN locations_location district ON clinic.parent_id=district.id
  LEFT JOIN locations_location province ON district.parent_id=province.id
  WHERE province.slug='luapula')