from mwana.settings import *

TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.run_tests'
TEST_OUTPUT_VERBOSE = True
TEST_OUTPUT_DESCRIPTIONS = True
TEST_OUTPUT_DIR = 'xmlrunner'

# for sqlite3:
#DATABASE_ENGINE = 'sqlite3'
#DATABASE_NAME = 'db.sqlite3'
#TEST_DATABASE_NAME = 'mwana-test.db'

# for postgresql:
DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'mwana_devel'
#DATABASE_USER = ''
#DATABASE_PASSWORD = ''
#DATABASE_HOST = ''
#DATABASE_PORT = ''
#TEST_DATABASE_NAME = 'test_mwana_devel'
