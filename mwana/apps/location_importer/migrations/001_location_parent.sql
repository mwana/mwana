BEGIN;
ALTER TABLE "locations_location"
ADD COLUMN "parent_id" integer;
CREATE INDEX "locations_location_parent_id" ON "locations_location" ("parent_id");
ALTER TABLE "locations_location" ADD CONSTRAINT "parent_id_refs_id_47ca058b" FOREIGN KEY ("parent_id") REFERENCES "locations_location" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;
