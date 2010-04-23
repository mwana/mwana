CREATE TABLE "rapidsms_contact_types" (
    "id" serial NOT NULL PRIMARY KEY,
    "contact_id" integer NOT NULL REFERENCES "rapidsms_contact" ("id") DEFERRABLE INITIALLY DEFERRED,
    "contacttype_id" integer NOT NULL REFERENCES "contactsplus_contacttype" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("contact_id", "contacttype_id")
);

