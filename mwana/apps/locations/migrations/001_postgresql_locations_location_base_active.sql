BEGIN;
ALTER TABLE locations_location_base ADD COLUMN active boolean;
COMMIT;