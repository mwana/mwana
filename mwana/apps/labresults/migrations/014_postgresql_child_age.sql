BEGIN;
ALTER TABLE labresults_result ALTER COLUMN child_age TYPE decimal(4,1);
COMMIT;
