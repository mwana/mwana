BEGIN;
ALTER TABLE issuetracking_issue ADD COLUMN desired_start_date date;
ALTER TABLE issuetracking_issue ADD COLUMN desired_completion_date date;
ALTER TABLE issuetracking_issue ADD COLUMN "open" boolean;
COMMIT;
