BEGIN;
ALTER TABLE rapidsms_contact
ADD COLUMN remind_id varchar(7);
COMMIT;
