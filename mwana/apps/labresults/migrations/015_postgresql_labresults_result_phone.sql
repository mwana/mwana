BEGIN;
ALTER TABLE labresults_result ADD COLUMN phone varchar(15);
COMMIT;
