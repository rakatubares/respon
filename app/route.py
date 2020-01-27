import threading, time
from datetime import datetime
from flask import render_template, request, jsonify
from flask_socketio import emit
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException, WebDriverException

from app import app, socketio
from app.controller.app.manifest import Manifest

def validate(noAju):
	noAju = ''.join(filter(str.isdigit, noAju))
	if len(noAju) != 26:
		return [0, 'Isikan no aju lengkap 26 digit']
	else:
		return [1, noAju]

def initiateManifest():
	print('Initiate manifest..')

	global manifest
	# global driverManifest
	manifest = Manifest()
	# manifest.openMenu()

def getResponseManifest(tglAwal, tglAkhir, noAju):
	respon = ''
	format1 = '%Y-%m-%d'
	format2 = '%d%m%y'
	tglAwal = datetime.strptime(tglAwal, format1).strftime(format2)
	tglAkhir = datetime.strptime(tglAkhir, format1).strftime(format2)

	isvalid = validate(noAju)
	if isvalid[0] == 0:
		return ['msg', isvalid[1]]
	else:
		noAju = isvalid[1]

	# while respon == '':
	# 	try:
	# 		if driverManifest not in globals():
	# 			initiateManifest()
	# 		respon = manifest.getResponses(tglAwal, tglAkhir, noAju)
	# 	except (NameError, InvalidSessionIdException) as e:
	# 		if 'manifest' in globals():
	# 			driverManifest.close()
	# 		initiateManifest()
			# raise e

			# try:
			# 	pass
			# except Exception as e:
			# 	raise e
			# else:
			# 	pass

	if 'manifest' not in globals():
		initiateManifest()
	respon = manifest.getResponses(tglAwal, tglAkhir, noAju)

	return ['respon', respon]
	# manifest.getResponses(tglAwal, tglAkhir, noAju)
	# return None

def validate2(noAju):
	isvalid = False
	tglAwal = ''
	# noAju = ''.join(filter(str.isdigit, aju))
	if len(noAju) != 26:
		emit('my_response', {'data': 'Isikan no aju lengkap 26 digit', 'time': getTime(), 'is_end': True})
	else:
		tglAju = noAju[12:20]
		try:
			dateAju = datetime.strptime(tglAju, '%Y%m%d')
		except Exception as e:
			emit('my_response', {'data': 'Tanggal aju tidak valid', 'time': getTime(), 'is_end': True})
		else:
			dateNow = datetime.now()
			if dateAju > dateNow:
				emit('my_response', {'data': 'Tanggal aju tidak boleh lebih dari hari ini', 'time': getTime(), 'is_end': True})
			else:
				tglAwal = dateAju.strftime('%d%m%y')
				isvalid = True
	return (isvalid, tglAwal)

def getResponseManifest2(noAju):
	isvalid, tglAwal = validate2(noAju)
	if isvalid == True:
		if 'manifest' not in globals():
			initiateManifest()
		while manifest.is_idle == False:
			time.sleep(2)
		else:
			manifest.getResponses(tglAwal, noAju)

def getTime():
	now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
	return now

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/respon', methods=['GET'])
def respon():
	respon = getResponseManifest(request.args['tglawal'], request.args['tglakhir'], request.args['aju'])
	return jsonify(respon)

@app.route('/click', methods=['GET'])
def click():
	msg = manifest.sendResponse(request.args['id'])
	return jsonify(msg)

# @socketio.on('connect')
# def onConnect():
# 	currentSocketId = request.sid
# 	emit('my_response', {'data': currentSocketId, 'time': getTime()})

@socketio.on('request_respon')
def requestRespon(aju):
	stop_event = threading.Event()
	aju = aju['data']
	noAju = ''.join(filter(str.isdigit, aju))
	emit('my_response', {'data': f'Mencari respon aju {aju}', 'time': getTime(), 'is_end': False})
	getResponseManifest2(aju)