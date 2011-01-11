BEGIN;
ALTER TABLE locations_location ADD COLUMN has_independent_printer boolean;
UPDATE locations_location SET has_independent_printer = false;
COMMIT;