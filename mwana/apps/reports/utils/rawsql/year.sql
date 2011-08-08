-- Function: "year"(timestamp with time zone)

-- DROP FUNCTION "year"(timestamp with time zone);

CREATE OR REPLACE FUNCTION "year"(timestamp with time zone)
  RETURNS integer AS
$BODY$
      SELECT EXTRACT(YEAR FROM $1)::INTEGER;
$BODY$
  LANGUAGE 'sql' STABLE
  COST 100;
ALTER FUNCTION "year"(timestamp with time zone) OWNER TO mwana;
-- Function: "year"(date)

-- DROP FUNCTION "year"(date);

CREATE OR REPLACE FUNCTION "year"(date)
  RETURNS integer AS
$BODY$
      SELECT EXTRACT(YEAR FROM $1)::INTEGER;
$BODY$
  LANGUAGE 'sql' IMMUTABLE
  COST 100;
ALTER FUNCTION "year"(date) OWNER TO mwana;
-- Function: "year"(timestamp without time zone)

-- DROP FUNCTION "year"(timestamp without time zone);

CREATE OR REPLACE FUNCTION "year"(timestamp without time zone)
  RETURNS integer AS
$BODY$ 
      SELECT EXTRACT(YEAR FROM $1)::INTEGER; 
$BODY$
  LANGUAGE 'sql' IMMUTABLE
  COST 100;
ALTER FUNCTION "year"(timestamp without time zone) OWNER TO mwana;
