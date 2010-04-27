-- make location slug unique only across the location type
BEGIN;
ALTER TABLE locations_location DROP CONSTRAINT locations_location_slug_key;
ALTER TABLE locations_location ADD UNIQUE ("slug", "type_id");
COMMIT;
