BEGIN;
ALTER TABLE labresults_result ADD COLUMN arrival_date timestamp with time zone;
COMMIT;
