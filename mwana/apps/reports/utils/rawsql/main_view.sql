-- View: reports_messagegroup

-- DROP VIEW reports_messagegroup;

CREATE OR REPLACE VIEW reports_messagegroup AS 
 SELECT messagelog_message.id, 
        CASE
            WHEN rapidsms_connection.identity IS NULL then rapidsms_contact.id::text
            ELSE rapidsms_connection.identity
        END::character varying(100) AS phone, 
        CASE
            WHEN rapidsms_connection.backend_id = 1 THEN 'zain'::text
            WHEN rapidsms_connection.backend_id = 2 THEN 'message tester'::text
            WHEN rapidsms_connection.backend_id = 3 THEN 'mtn'::text
            WHEN rapidsms_connection.backend_id = 4 THEN 'zain1'::text
            ELSE NULL::text
        END::character varying(15) AS backend, messagelog_message.direction, messagelog_message.date, messagelog_message.text, 
        CASE
            WHEN btrim(messagelog_message.text) ~~* 'msg cba%'::text THEN 'MSG CBA'::text
            WHEN btrim(messagelog_message.text) ~~* 'msg dho%'::text THEN 'MSG DHO'::text
            WHEN btrim(messagelog_message.text) ~~* 'msg clinic%'::text THEN 'MSG CLINIC'::text
            WHEN btrim(messagelog_message.text) ~~* 'msg all%'::text THEN 'MSG ALL'::text
            WHEN btrim(messagelog_message.text) ~~* 'sent%'::text THEN 'SENT'::text
            WHEN btrim(messagelog_message.text) ~~* 'received%'::text THEN 'RECEIVED'::text
            WHEN btrim(messagelog_message.text) ~~* 'result%'::text THEN 'RESULT'::text
            WHEN btrim(messagelog_message.text) ~~* 'told%'::text THEN 'TOLD'::text
            WHEN btrim(messagelog_message.text) ~~* 'confirm%'::text THEN 'CONFIRM'::text
            WHEN btrim(messagelog_message.text) ~~* 'comfirm%'::text THEN 'CONFIRM'::text
            WHEN btrim(messagelog_message.text) ~~* 'comfem%'::text THEN 'CONFIRM'::text
            WHEN btrim(messagelog_message.text) ~~* 'confem%'::text THEN 'CONFIRM'::text
            WHEN btrim(messagelog_message.text) ~~* 'help%'::text THEN 'HELP'::text
            WHEN btrim(messagelog_message.text) ~~* 'leave%'::text THEN 'LEAVE'::text
            WHEN btrim(messagelog_message.text) ~~* 'check%'::text THEN 'CHECK'::text
            WHEN btrim(messagelog_message.text) ~~* 'trace%'::text THEN 'TRACE'::text
            WHEN btrim(messagelog_message.text) ~~* 'join%'::text THEN 'JOIN'::text
            WHEN btrim(messagelog_message.text) ~~* 'agent%'::text THEN 'AGENT'::text
            WHEN btrim(messagelog_message.text) ~~* 'birth%'::text THEN 'BIRTH'::text
            WHEN btrim(messagelog_message.text) ~~* 'mwana%'::text THEN 'MWANA'::text
            WHEN btrim(messagelog_message.text) ~~* 'cba%'::text THEN 'CBA'::text
            WHEN btrim(messagelog_message.text) ~~* 'all%'::text THEN 'ALL'::text
            WHEN btrim(messagelog_message.text) ~~* 'clinic%'::text THEN 'CLINIC'::text
            WHEN btrim(messagelog_message.text) ~~* 'invalid%'::text THEN 'INVALID'::text
            WHEN btrim(messagelog_message.text) ~~* '% to all]'::text THEN 'TO ALL'::text
            WHEN btrim(messagelog_message.text) ~~* '% to cba]'::text THEN 'TO CBA'::text
            WHEN btrim(messagelog_message.text) ~~* '% to clinic]'::text THEN 'TO CLINIC'::text
            WHEN btrim(messagelog_message.text) ~~* '%Please make sure your code is a 4-digit number like 1234%'::text THEN 'BAD CODE'::text
            ELSE NULL::text
        END::character varying(15) AS keyword, 
        CASE
            WHEN btrim(messagelog_message.text) ~~* 'Make a followup for changed results%'::text THEN true
            WHEN btrim(messagelog_message.text) ~~* 'URGENT:%'::text THEN true
            ELSE false
        END AS changed_res, 
        CASE
            WHEN btrim(messagelog_message.text) ~~* '%test results ready for you. Please reply to%'::text THEN true
            ELSE false
        END AS new_results, ''::character varying(10) AS app, contactsplus_contacttype.name AS contact_type, 
        CASE
            WHEN locations_locationtype.slug::text = 'zone'::text THEN parentlocation.name
            ELSE mylocation.name
        END AS clinic, 
        CASE
            WHEN messagelog_message.date >= '2010-06-14 01:00:00+03'::timestamp with time zone THEN false
            WHEN messagelog_message.date < '2010-06-14 01:00:00+03'::timestamp with time zone THEN true
            ELSE NULL::boolean
        END AS before_pilot
   FROM messagelog_message
   LEFT JOIN rapidsms_connection ON rapidsms_connection.id = messagelog_message.connection_id
   LEFT JOIN rapidsms_contact ON rapidsms_contact.id = messagelog_message.contact_id
   LEFT JOIN rapidsms_contact_types ON rapidsms_contact_types.contact_id = messagelog_message.contact_id
   LEFT JOIN contactsplus_contacttype ON contactsplus_contacttype.id = rapidsms_contact_types.contacttype_id
   LEFT JOIN locations_location mylocation ON mylocation.id = rapidsms_contact.location_id
   LEFT JOIN locations_location parentlocation ON parentlocation.id = mylocation.parent_id
   LEFT JOIN locations_locationtype ON locations_locationtype.id = mylocation.type_id;

--ALTER TABLE reports_messagegroup OWNER TO mwana;

