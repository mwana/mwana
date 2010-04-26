BEGIN;
ALTER TABLE "locations_location"
ADD COLUMN "parent_id" integer;
CREATE INDEX "locations_location_parent_id" ON "locations_location" ("parent_id");
COMMIT;