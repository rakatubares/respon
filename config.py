import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	# database
    SQLALCHEMY_DATABASE_URI = 'mysql://root@localhost/db_respon'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ceisa
    CEISA_USER = 'hanief.wicaksono'
    CEISA_PASSWORD = 'ubb9ghij2yivn'