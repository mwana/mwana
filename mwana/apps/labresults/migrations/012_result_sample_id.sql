BEGIN;
ALTER TABLE labresults_result
    ALTER COLUMN sample_id TYPE varchar(20);
COMMIT;
