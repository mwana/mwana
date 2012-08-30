BEGIN;
ALTER TABLE websmssender_websmslog ADD COLUMN "admins_notified" boolean;
COMMIT;
