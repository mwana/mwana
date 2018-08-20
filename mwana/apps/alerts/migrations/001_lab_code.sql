BEGIN;
ALTER TABLE "alerts_lab" ADD COLUMN "lab_code" varchar(50);
COMMIT;
