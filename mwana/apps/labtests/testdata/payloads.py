# vim: ai ts=4 sts=4 et sw=4
"""
Defines some test data payloads
"""
#a simple raw json payload with three client results records
INITIAL_PAYLOAD = {
    "source": "ndola/arthur-davison",
    "now": "2010-04-22 10:30:00",
    "version": "1.0",
    "info": "sync",
    "logs": [
        {
            "msg": "booting daemon...",
            "lvl": "INFO",
            "at": "2010-04-22 07:18:03,140"
        },
        {
            "msg": "archiving 124 records",
            "lvl": "INFO",
            "at": "2010-04-22 09:18:23,248"
        }
    ],
    "samples": [
        {
            "coll_on": "2010-03-31",
            "hw": "BEYONSE KNOWS",
            "mother_age": 19,
            "result_detail": None,
            "sync": "new",
            "sex": "f",
            "result": "Detected",
            "test_type": "dbs",
            "recv_on": "2010-04-08",
            "fac": '402029',
            "id": "EID10-09999",
            "hw_tit": "NURSE",
            "pat_id": "EID78",
            "dob": "2010-02-08",
            "proc_on": "2010-04-11",
        },
        {
            "coll_on": "2010-03-31",
            "hw": "JANE SMITH",
            "mother_age": 19,
            "result_detail": None,
            "sync": "new",
            "sex": "f",
            "result": "100",
            "recv_on": "2010-04-08",
            "fac": '402029',
            "id": "10-09999",
            "hw_tit": "NURSE",
            "pat_id": "78",
            "dob": "2010-02-08",
            "proc_on": "2010-04-11",
            "unit": 'p/mL'
        },
        {
            "coll_on": "2010-03-25",
            "hw": "JENNY HOWARD",
            "mother_age": 41,
            "result_detail": None,
            "sync": "new",
            "sex": "f",
            "result": "200",
            "recv_on": "2010-04-11",
            "fac": '402029',
            "id": "10-09998",
            "hw_tit": "AMM",
            "pat_id": "1029023412",
            "dob": "2009-03-30",
            "proc_on": "2010-04-13",
            "unit": 'p/mL'
        },
        {
            "coll_on": "2010-04-08",
            "hw": "MOLLY",
            "mother_age": 31,
            "result_detail": None,
            "sync": "new",
            "sex": "f",
            "result": "300",
            "recv_on": "2010-04-15",
            "fac": '402029',
            "id": "10-09997",
            "hw_tit": "ZAN",
            "pat_id": "212987",
            "dob": "2010-01-12",
            "proc_on": "2010-04-17",
            "unit": 'p/mL',
            "phone": '+260977212112'
        }
    ]
}

