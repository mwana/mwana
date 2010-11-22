BEGIN;
ALTER TABLE locations_location ADD COLUMN send_live_results boolean;
UPDATE locations_location SET send_live_results = false;
ALTER TABLE locations_location ALTER COLUMN send_live_results SET NOT NULL;
COMMIT;

