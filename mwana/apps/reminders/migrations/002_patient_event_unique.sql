ALTER TABLE reminders_patientevent ADD UNIQUE ("patient_id", "event_id", "date");
