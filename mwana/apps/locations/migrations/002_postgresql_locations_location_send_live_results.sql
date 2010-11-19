BEGIN;
ALTER TABLE locations_location ADD COLUMN send_live_results boolean;
COMMIT;

