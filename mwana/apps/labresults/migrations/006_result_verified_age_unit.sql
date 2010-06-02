BEGIN;
ALTER TABLE labresults_result ADD COLUMN verified boolean;
ALTER TABLE labresults_result ADD COLUMN child_age_unit varchar(20);
COMMIT;
