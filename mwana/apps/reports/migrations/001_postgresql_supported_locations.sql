INSERT INTO reports_supportedlocation (location_id,supported)
SELECT DISTINCT id,true from locations_location
WHERE slug IN ('402026',
  '402030',
  '402023',
  '403011',
  '403017',
  '403029',
  '403032',
  '403012',
  '406013',
  '406015',
  '406016',
  '808014',
  '808030',
  '808015',
  '808025',
  '808021',
  '807099',
  '807033',
  '807026',
  '807035',
  '807037')
  ORDER BY id