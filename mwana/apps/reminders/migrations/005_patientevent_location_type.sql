BEGIN;
ALTER TABLE reminders_patientevent ADD COLUMN event_location_type varchar(5);
COMMIT;
