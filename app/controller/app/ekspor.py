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

class Ekspor(object):
	"""docstring for Ekspor"""
	def __init__(self):
		super(Ekspor, self).__init__()
		self.url = 'http://manif-in.customs.go.id/beacukai-manifes'
		self.ceisa_app = 'manifest'
		self.is_idle = True
		self.driver = ''
		self.openMenu()

	def openPage(self):
		log = Login(self.url, self.ceisa_app)
		self.driver = log.login()

	def openMenu(self):
		self.is_idle = False
		self.openPage()

		print('Open menu..')
		menuInformasi = self.driver.find_element_by_css_selector('.z-menu:nth-child(1) button')
		menuInformasi.click()

		menuRespon = self.driver.find_element_by_css_selector('.z-menu-popup li:nth-child(3) a')
		menuRespon.click()

		pre.waitLoading(self.driver)
		self.is_idle = True

	def getResponses(self, tglAwal, noAju):
		self.is_idle = False

		# Create request id in database
		req = Request(app=self.ceisa_app, aju=noAju)
		db.session.add(req)
		db.session.commit()
		self.req_id = req.id

		# Store request start in status table
		sta = Status(id_request=self.req_id, status='start')
		db.session.add(sta)
		db.session.commit()

		try:
			checkInputTgl = EC.presence_of_element_located((By.CLASS_NAME, 'z-datebox-inp'))
			WebDriverWait(self.driver, 10).until(checkInputTgl)
		except TimeoutException:
			print('Timeout to load page..')

			# Store error in status table
			msg = 'Gagal membuka halaman pencarian. Coba beberapa saat lagi.'
			is_end = True
			self.updateStatus(msg, is_end)
		except Exception as e:
			raise e
		else:
			print('Collect responses..')

			# Update status table
			msg = 'Mencari respon'
			self.updateStatus(msg)

			self.find_peb()

	def find_peb(self):
		tabPeb = self.driver.find_element_by_css_selector('.z-tab:nth-child(1)')
		tabPeb.click()

		inputTglAwal = self.driver.find_element_by_css_selector('.z-datebox-inp')
		dropFilter = self.driver.find_element_by_css_selector('input.z-combobox-inp')
		optionCar = self.driver.find_element_by_css_selector('tr.z-comboitem:nth-child(4)')