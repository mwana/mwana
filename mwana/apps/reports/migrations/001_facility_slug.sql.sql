BEGIN;
ALTER TABLE reports_messagebylocationusertypebackend
    ALTER COLUMN facility_slug TYPE varchar(10);
COMMIT;
BEGIN;

ALTER TABLE reports_messagebylocationbybackend
    ALTER COLUMN facility_slug TYPE varchar(10);
COMMIT;

ALTER TABLE reports_messagebylocationbyusertype
    ALTER COLUMN facility_slug TYPE varchar(10);
COMMIT;