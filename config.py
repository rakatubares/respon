import os
basedir = os.path.abspath(os.path.dirname(__file__))

class ProductionConfig(object):
	# flask
	SECRET_KEY = '123456'

	# database
	SQLALCHEMY_DATABASE_URI = 'mysql://root@localhost/db_respon'
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	# ceisa
	CEISA_USER = 'hanief.wicaksono'
	CEISA_PASSWORD = 'ubb9ghij2yivn'

class DevelopmentConfig(object):
	# flask
	SECRET_KEY = '123456'
	DEBUG = False
	FLASK_DEBUG = 0

	# database
	SQLALCHEMY_DATABASE_URI = 'mysql://root@localhost/db_respon_dev'
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	# ceisa
	CEISA_USER = 'hanief.wicaksono'
	CEISA_PASSWORD = 'ubb9ghij2yivn'