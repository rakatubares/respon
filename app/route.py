from datetime import datetime
from flask import render_template, request, jsonify
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException, WebDriverException

from app import app
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
	global driverManifest
	manifest = Manifest()
	driverManifest = manifest.openMenu()

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
	# 		if 'driverManifest' in globals():
	# 			driverManifest.close()
	# 		initiateManifest()
			# raise e

			# try:
			# 	pass
			# except Exception as e:
			# 	raise e
			# else:
			# 	pass

	if 'driverManifest' not in globals():
		initiateManifest()
	respon = manifest.getResponses(tglAwal, tglAkhir, noAju)

	return ['respon', respon]
	# manifest.getResponses(tglAwal, tglAkhir, noAju)
	# return None

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/respon', methods=['GET'])
def respon():
	respon = getResponseManifest(request.args['tglawal'], request.args['tglakhir'], request.args['aju'])
	return jsonify(respon)

@app.route('/click', methods=['GET'])
def click():
	msg = driverManifest.sendResponse(request.args['id'])
	return jsonify(msg)