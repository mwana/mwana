from mwana.zambia.settings_country import *

TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.run_tests'
TEST_OUTPUT_VERBOSE = True
TEST_OUTPUT_DESCRIPTIONS = True
TEST_OUTPUT_DIR = 'zambia/xmlrunner'

# for sqlite3:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
# since we might hit the database from any thread during testing, the
# in-memory sqlite database isn't sufficient. it spawns a separate
# virtual database for each thread, and syncdb is only called for the
# first. this leads to confusing "no such table" errors. We create
# a named temporary instance instead.
        "TEST_NAME": "/dev/shm/test_db.sqlite3",
    }
}

# for postgresql:
#DATABASES = {
#    "default": {
#        "ENGINE": "django.db.backends.postgresql_psycopg2",
#        "NAME": "mwana_legacy",
#        "USER": "",
#        "PASSWORD": "",
#        "HOST": "",
#    }
#}

