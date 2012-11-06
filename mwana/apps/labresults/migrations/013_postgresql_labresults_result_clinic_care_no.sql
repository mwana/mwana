BEGIN;
ALTER TABLE labresults_result ADD COLUMN clinic_care_no varchar(50);
COMMIT;
