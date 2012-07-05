# vim: ai ts=4 sts=4 et sw=4

from mwana.logemailer import TlsSMTPHandler
from mwana.logemailer import logging
from mwana.zambia.settings_country import *

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PASSWORD = 'fakepassword'
EMAIL_HOST_USER = 'sinkalat@gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True


logger = logging.getLogger()

gm = TlsSMTPHandler(("smtp.gmail.com", 587), EMAIL_HOST_USER,
                    ['sinkalation@gmail.com'], 'Error found in router!',
                    (EMAIL_HOST_USER, EMAIL_PASSWORD))
gm.setLevel(logging.ERROR)

logger.addHandler(gm)