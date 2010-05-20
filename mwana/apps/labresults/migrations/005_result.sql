BEGIN;
ALTER TABLE labresults_result
ADD COLUMN record_change varchar(6);
ALTER TABLE labresults_result
ADD COLUMN old_value varchar(50)
COMMIT;
