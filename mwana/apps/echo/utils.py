# vim: ai ts=4 sts=4 et sw=4
from django.utils.functional import curry
from rapidsms.contrib.ajax.utils import call_router


# these helper methods are just proxies to app.py
get_backend_status = curry(call_router, "echo", "status")
get_send_test_message   = curry(call_router, "echo", "send_test_message")
get_available_backends = curry(call_router, "echo", "available_backends")
