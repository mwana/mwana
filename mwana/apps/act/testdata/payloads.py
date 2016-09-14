# vim: ai ts=4 sts=4 et sw=4

from datetime import date
from datetime import timedelta

"""
Defines some test data payloads
"""

CLIENT_PAYLOAD = {
    "now": "2016-08-21 11:54:40",
    "info": "client",
    "version": "0.1",
    "client": {
        "uuid": "f9f7ce6f-050f-40f3-b904-d49b60539c58",
        "nupin": "12313131",
        "alias": "TK-14141414141",
        "dob": "2016-08-21",
        "sex": "m",
        "address": "1",
        "art_num": "14141414141",
        "sms_on": True,
        "location": "402029",
        "zone": "1",
        "phone": "+260979236339",
        "lab_msg": "m3",
        "phar_msg": "m2"
    }
}

CHW_PAYLOAD = {
    "now": "2016-08-21 18:08:56",
    "info": "chw",
    "version": "0.1",
    "chw": {
        "uuid": "d3ee80b7-67e6-423b-9db5-a34a79a2c01a",
        "national_id": "1321313",
        "name": "Trevor Sinkala",
        "village": "Kwatu",
        "location": "402029",
        "zone": "1",
        "phone": "+260979599999"
    }
}

LAB_APPOINTMENT_PAYLOAD = {
    "now": "2016-08-21 18:08:56",
    "info": "appointment",
    "version": "0.1",
    "appointment": {
        "uuid": "f5936299-f07a-49d0-9145-c2fcb8458a28",
        "client": "f9f7ce6f-050f-40f3-b904-d49b60539c58",
        "chw": "d3ee80b7-67e6-423b-9db5-a34a79a2c01a",
        "type": "Lab",
        "date": (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    }
}

PHARMACY_APPOINTMENT_PAYLOAD = {
    "now": "2016-08-21 18:08:56",
    "info": "appointment",
    "version": "0.1",
    "appointment": {
        "uuid": "app2",
        "client": "f9f7ce6f-050f-40f3-b904-d49b60539c58",
        "chw": "d3ee80b7-67e6-423b-9db5-a34a79a2c01a",
        "type": "pharmacy",
        "date": (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')
    }
}