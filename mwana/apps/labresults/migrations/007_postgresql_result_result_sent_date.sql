BEGIN;
ALTER TABLE labresults_result ADD COLUMN result_sent_date timestamp with time zone;
COMMIT;
