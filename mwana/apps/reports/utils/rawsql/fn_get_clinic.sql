
CREATE OR REPLACE FUNCTION "clinic"(character varying(6))
  RETURNS character varying(100) AS
$BODY$
      
select "name" from locations_location where type_id<>8 and (slug in (select regexp_split_to_table($1, E'\\s+'))
or slug||'0' in (select regexp_split_to_table($1, E'\\s+')))
$BODY$
  LANGUAGE 'sql' STABLE