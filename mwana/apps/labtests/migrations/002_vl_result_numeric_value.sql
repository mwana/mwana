BEGIN;
ALTER TABLE "labtests_result" ADD COLUMN  "numeric_result" integer CHECK ("numeric_result" >= 0);
COMMIT;

