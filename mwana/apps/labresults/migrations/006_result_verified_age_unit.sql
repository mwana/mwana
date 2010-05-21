BEGIN;
ALTER TABLE labresults_payload ADD COLUMN verified boolean;
ALTER TABLE labresults_payload ADD COLUMN child_age_unit varchar(20);
COMMIT;
