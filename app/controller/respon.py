import threading, time
from bs4 import BeautifulSoup
from datetime import datetime
from flask_socketio import emit
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app import app, db, socketio
from app.controller import preprocess as pre
from app.controller.login import Login
from app.models import Request, Status

class Respon(object):
	"""docstring for Respon"""
	def __init__(self, url, ceisa_app):
		super(Respon, self).__init__()
		self.url = url
		self.ceisa_app = ceisa_app
		self.is_idle = True
		self.driver = ''
		self.openMenu()
		self.alwaysOn()
		
	def openPage(self):
		log = Login(self.url, self.ceisa_app)
		self.driver = log.login()
		# return self.driver

	def openMenu(self):
		self.is_idle = False
		self.openPage()

		print('Open menu..')
		menuUtility = self.driver.find_element_by_css_selector('.z-menu:nth-child(4) button')
		menuUtility.click()

		menuRespon = self.driver.find_element_by_css_selector('.z-menu-popup li:nth-child(1) a')
		menuRespon.click()

		pre.waitLoading(self.driver)
		self.is_idle = True

	def updateRequest(self):
		# Update nama perusahaan ke request table
		request = Request.query.filter_by(id=self.req_id).first()
		perusahaan = self.responses[0][1]
		request.perusahaan = perusahaan
		db.session.commit()

	def updateStatus(self, msg, end=False):
		sta = Status(id_request=self.req_id, status=msg)
		db.session.add(sta)
		db.session.commit()
		emit('my_response', {'data': msg, 'time': self.getTime(), 'is_end': end})

	def getTime(self):
		now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
		return now

	def alwaysOn(self):
		threading.Timer(300, self.alwaysOn).start()
		self.is_idle = False
		checkInputTgl = EC.presence_of_element_located((By.CLASS_NAME, 'z-datebox-inp'))
		WebDriverWait(self.driver, 10).until(checkInputTgl)
		print('always on')
		btnDate = self.driver.find_element_by_css_selector('.z-datebox-btn')
		btnDate.click()
		time.sleep(1)
		btnDate.click()
		self.is_idle = True