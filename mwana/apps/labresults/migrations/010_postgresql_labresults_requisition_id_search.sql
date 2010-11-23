BEGIN;
ALTER TABLE labresults_result ADD COLUMN requisition_id_search varchar(50);
UPDATE labresults_result SET requisition_id_search = replace(requisition_id, '-', '');
COMMIT;
ALTER TABLE labresults_result ALTER COLUMN requisition_id_search SET NOT NULL;

