BEGIN;
ALTER TABLE "act_historicalevent" ADD COLUMN "fact_day" varchar(20);
COMMIT;
