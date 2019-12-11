import flask
# from bs4 import BeautifulSoup
from datetime import datetime
from flask import render_template, request, jsonify

from controller.app.manifest import Manifest

app = flask.Flask(__name__, template_folder='view', static_folder='assets')
app.config["DEBUG"] = True

def manifest(tglAwal, tglAkhir, noAju):
	format1 = '%Y-%m-%d'
	format2 = '%d%m%y'
	tglAwal = datetime.strptime(tglAwal, format1).strftime(format2)
	tglAkhir = datetime.strptime(tglAkhir, format1).strftime(format2)
	# return [tglAwal, tglAkhir, noAju]

	manif = Manifest()
	# respon = manif.getResponses('051219', '151219', '18052829061820191207000012')
	respon = manif.getResponses(tglAwal, tglAkhir, noAju)
	return respon

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/respon', methods=['GET'])
def respon():
	respon = manifest(request.args['tglawal'], request.args['tglakhir'], request.args['aju'])
	return jsonify(respon)

app.run()