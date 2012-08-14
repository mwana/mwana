BEGIN;
ALTER TABLE issuetracking_issue ADD COLUMN dev_time varchar(160);
COMMIT;
