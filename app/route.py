import threading, time
from datetime import datetime
from flask import render_template, request, jsonify
from flask_socketio import emit
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException, WebDriverException

from respon import app, socketio
from app.controller.app.manifest import Manifest
from app.controller.app.ekspor import Ekspor

def switchRespon(jnsAju, noAju):
	switcher = {
		'Manifest': getResponseManifest,
		'PEB': getResponsePeb,
		'PIB': getResponsePib
	}
	# Get the function from switcher dictionary
	func = switcher.get(jnsAju, returnAjuNotFound)
	# Execute the function
	return func(noAju)

def returnAjuNotFound(noAju):
	emit('my_response', {'data': f'Jenis aju tidak ditemukan', 'time': getTime(), 'is_end': True})

def initiateManifest():
	print('Initiate manifest..')

	global manifest
	manifest = Manifest()

def getResponseManifest(noAju):
	emit('my_response', {'data': f'Processing Manifest aju {noAju}', 'time': getTime(), 'is_end': False})
	isvalid, tglAwal = validate(noAju)
	tglAkhir = getDate()
	if isvalid == True:
		if 'manifest' not in globals():
			initiateManifest()
		while manifest.is_idle == False:
			time.sleep(2)
		else:
			manifest.getResponses(tglAwal, tglAkhir, noAju)

def initiateEkspor():
	print('Initiate peb..')

	global ekspor
	ekspor = Ekspor()

def getResponsePeb(noAju):
	emit('my_response', {'data': f'Processing PEB aju {noAju}', 'time': getTime(), 'is_end': False})
	isvalid, tglAwal = validate(noAju)
	tglAkhir = getDate()
	if isvalid == True:
		if 'ekspor' not in globals():
			initiateEkspor()
		while ekspor.is_idle == False:
			time.sleep(2)
		else:
			ekspor.getResponses(tglAwal, tglAkhir, noAju)

def getResponsePib(noAju):
	# emit('my_response', {'data': f'Processing PIB aju {noAju}', 'time': getTime(), 'is_end': True})
	emit('my_response', {'data': f'Kirim ulang respon PIB belum tersedia', 'time': getTime(), 'is_end': True})

def validate(noAju):
	isvalid = False
	tglAwal = ''

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

def getTime():
	now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
	return now

def getDate():
	now = datetime.now().strftime('%d%m%y')
	return now

@app.route('/')
def index():
	return render_template('index.html')

@socketio.on('request_respon')
def requestRespon(data):
	stop_event = threading.Event()
	jnsAju = data['jnsaju']
	noAju = data['noaju']
	noAju = ''.join(filter(str.isdigit, noAju))

	if jnsAju == None:
		emit('my_response', {'data': f'Pilih jenis aju dulu', 'time': getTime(), 'is_end': True})
	else:
		switchRespon(jnsAju, noAju)