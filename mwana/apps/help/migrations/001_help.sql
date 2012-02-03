BEGIN;
ALTER TABLE help_helprequest ADD COLUMN addressed_on timestamp with time zone;
ALTER TABLE "help_helprequest" ADD COLUMN "resolved_by" varchar(160);
ALTER TABLE "help_helprequest" ADD COLUMN "notes" varchar(255);
COMMIT;
