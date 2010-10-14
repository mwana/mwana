BEGIN;
ALTER TABLE labresults_result ADD COLUMN arrival_date datetime;
COMMIT;
