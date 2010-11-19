BEGIN;
ALTER TABLE locations_location ADD COLUMN active boolean;
COMMIT;
