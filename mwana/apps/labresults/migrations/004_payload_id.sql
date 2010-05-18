BEGIN;
ALTER TABLE labresults_result ADD COLUMN payload_id integer;
ALTER TABLE "labresults_result" ADD CONSTRAINT "payload_id_refs_id_ee61ee27" FOREIGN KEY ("payload_id") REFERENCES "labresults_payload" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE labresults_lablog RENAME COLUMN payload_id_id TO payload_id;
COMMIT;
