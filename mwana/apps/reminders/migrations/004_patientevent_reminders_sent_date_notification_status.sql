BEGIN;
ALTER TABLE reminders_patientevent ADD COLUMN notification_status varchar(15);
ALTER TABLE reminders_patientevent ADD COLUMN notification_sent_date timestamp with time zone;
UPDATE reminders_patientevent SET notification_status = 'sent' WHERE notification_status isnull;
UPDATE reminders_patientevent SET notification_sent_date = '2010-10-01' WHERE notification_sent_date isnull;
COMMIT;
