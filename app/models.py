from app import db
# from sqlalchemy import text

class SignIn(db.Model):
	__tablename__ = 'login'
	id = db.Column(db.Integer, primary_key=True)
	hash = db.Column(db.String(32), index=True, nullable=False)
	status = db.Column(db.String(32), index=True, nullable=False)
	created_at = db.Column(db.TIMESTAMP, server_default=db.text('CURRENT_TIMESTAMP'), nullable=False)

class Request(db.Model):
	__tablename__ = 'request'
	id = db.Column(db.Integer, primary_key=True)
	app = db.Column(db.String(16), index=True, nullable=False)
	aju = db.Column(db.String(32), index=True, nullable=False)
	perusahaan = db.Column(db.String(64), index=True, nullable=True)
	created_at = db.Column(db.TIMESTAMP, server_default=db.text('CURRENT_TIMESTAMP'), nullable=False)
	children = db.relationship('Status')

class Status(db.Model):
	__tablename__ = 'request_status'
	id = db.Column(db.Integer, primary_key=True)
	id_request = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
	status = db.Column(db.String(32), index=True, nullable=False)
	created_at = db.Column(db.TIMESTAMP, server_default=db.text('CURRENT_TIMESTAMP'), nullable=False)