BEGIN;
ALTER TABLE issuetracking_issue ADD COLUMN percentage_complete integer;
COMMIT;
BEGIN;
UPDATE issuetracking_issue SET percentage_complete = 100 WHERE status in ('completed', 'bugfixed');
COMMIT;