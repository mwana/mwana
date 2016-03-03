BEGIN;
ALTER TABLE "labtests_result" ADD COLUMN "test_type" varchar(20);
COMMIT;

BEGIN;
UPDATE "labtests_result" SET "test_type" = 'vl' WHERE "test_type" IS NULL;
COMMIT;

