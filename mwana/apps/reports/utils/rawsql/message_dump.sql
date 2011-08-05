SELECT *
FROM reports_messagegroup
WHERE before_pilot='f' 
AND backEND <> 'message tester'
and contact_type <> 'DBS Printer'

--order by 1,2,3,4

;
