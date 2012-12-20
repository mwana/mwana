BEGIN;
ALTER TABLE people_person
    ADD COLUMN action_taken varchar(100);
COMMIT;
