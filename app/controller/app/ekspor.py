import html, threading, time
from bs4 import BeautifulSoup
from datetime import datetime
from flask_socketio import emit
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from respon import app, db, socketio
from app.controller import preprocess as pre
from app.controller.login import Login
from app.models import Request, Status

class Ekspor(object):
	"""docstring for Ekspor"""
	def __init__(self):
		super(Ekspor, self).__init__()
		self.url = 'http://ekspor.customs.go.id/beacukai-ekspor/'
		self.ceisa_app = 'ekspor'
		self.is_idle = True
		self.driver = ''
		self.openMenu()
		self.alwaysOn()

	def openPage(self):
		log = Login(self.url, self.ceisa_app)
		self.driver = log.login()

	def openMenu(self):
		self.is_idle = False
		self.openPage()
		print('Open menu..')

		# Klik menu informasi
		menuInformasi = self.driver.find_element_by_xpath('//button[@class = "z-menu-btn" and contains(., "Informasi")]')
		menuInformasi.click()

		# Klik submenu Cetak dan Kirim Ulang Respon
		checkMenuRespon = EC.presence_of_element_located((By.XPATH, '//ul[@class = "z-menu-popup-cnt"]//a[.= " Cetak dan Kirim Ulang Respon"]'))
		WebDriverWait(self.driver, 30).until(checkMenuRespon)

		menuRespon = self.driver.find_element_by_xpath('//ul[@class = "z-menu-popup-cnt"]//a[.= " Cetak dan Kirim Ulang Respon"]')
		menuRespon.click()
		pre.waitLoading(self.driver)

		# Pilih filter car
		checkFilter = EC.presence_of_element_located((By.XPATH, '//div[@class = "z-tabpanels"]/div[@class = "z-tabpanel"][1]//input[@class = "z-combobox-inp z-combobox-readonly"]'))
		WebDriverWait(self.driver, 120).until(checkFilter)

		dropFilter = self.driver.find_element_by_xpath('//div[@class = "z-tabpanels"]/div[@class = "z-tabpanel"][1]//input[@class = "z-combobox-inp z-combobox-readonly"]')
		dropFilter.click()

		optionCar = self.driver.find_element_by_xpath('//td[@class = "z-comboitem-text" and contains(., "Car")]')
		optionCar.click()

		checkInputAju = EC.presence_of_element_located((By.XPATH, '//div[@class = "z-tabpanels"]/div[@class = "z-tabpanel"][1]//input[@class = "z-textbox" and @maxlength="26"]'))
		WebDriverWait(self.driver, 120).until(checkInputAju)

		self.is_idle = True

	def getResponses(self, tglAwal, tglAkhir, noAju):
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
			self.find_peb(tglAwal, tglAkhir, noAju)

		self.is_idle = True

	def find_peb(self, tglAwal, tglAkhir, noAju):
		tabPeb = self.driver.find_element_by_xpath('//span[@class = "z-tab-text" and .= "PEB"]')
		tabPeb.click()

		inputTglAwal, inputTglAkhir = self.driver.find_elements_by_xpath('//div[@class = "z-tabpanels"]/div[@class = "z-tabpanel"][1]//input[@class = "z-datebox-inp"]')

		# Handling input tgl akhir
		inputTglAkhir.clear()
		inputTglAkhir.click()
		self.driver.execute_script('arguments[0].value = arguments[1]', inputTglAkhir, tglAkhir)
		inputTxt = self.driver.find_element_by_css_selector('.z-textbox')
		inputTxt.click()

		# Handling input tgl awal
		inputTglAwal.clear()
		inputTglAwal.click()
		self.driver.execute_script('arguments[0].value = arguments[1]', inputTglAwal, tglAwal)
		inputTxt = self.driver.find_element_by_css_selector('.z-textbox')
		inputTxt.click()

		# Handling filter no aju
		inputAju = self.driver.find_element_by_xpath('//div[@class = "z-tabpanels"]/div[@class = "z-tabpanel"][1]//input[@class = "z-textbox" and @maxlength="26"]')
		self.driver.execute_script('arguments[0].value = arguments[1]', inputAju, noAju)
		inputAju.click()

		# Klik tampilkan
		btnTampilkan = self.driver.find_element_by_xpath('//td[@class = "z-button-cm" and .= "Tampilkan"]')
		btnTampilkan.click()

		time.sleep(1)
		pre.waitLoading(self.driver, 120)
		try:
			errorBox = ''
			errorBox = self.driver.find_element_by_xpath('//div[contains(@class, "z-messagebox")]/span[contains(@class, "z-label") and contains(., "Unknown exception")]')
			while 'errorBox' != '':
				self.getResponses(tglAwal, noAju)
		except NoSuchElementException:
			try:
				boxNotFound = self.driver.find_element_by_xpath('//div[@class = "z-window-modal-cnt" and //span[@class = "z-label" and .= "Data Tidak Ditemukan"]]')
			except NoSuchElementException:
				print('catch element')
				noAjuDash = noAju[:6] + '-' + noAju[6:12] + '-' + noAju[12:20] + '-' + noAju[20:]
				rowPeb = self.driver.find_element_by_xpath(f'//div[@class = "z-listbox"][1]//tbody[contains(@id, "rows")]/tr[contains(@class, "z-listitem") and //div[@class = "z-listcell-cnt" and .= "{noAjuDash}"]]')

				colsHeader = rowPeb.find_elements_by_css_selector('td > div')
				noPeb = colsHeader[0].get_attribute('innerHTML')
				tglPeb = colsHeader[1].get_attribute('innerHTML')
				eksportir = colsHeader[2].get_attribute('innerHTML')
				ppjk = colsHeader[3].get_attribute('innerHTML')
				perusahaan = ppjk if ppjk != '-' else eksportir

				self.updateStatus(f'PEB no {noPeb} tgl {tglPeb} ditemukan')

				self.driver.execute_script('arguments[0].click()', rowPeb)
				time.sleep(.5)
				pre.waitLoading(self.driver)

				rows = self.driver.find_elements_by_xpath('//div[@class = "z-listbox"][2]//tbody[contains(@id, "rows")]/tr')
				self.updateRequest(perusahaan)
				self.chooseResponses(rows)
			else:
				btnOkNotFound = self.driver.find_element_by_xpath('//div[@class = "z-window-modal-cnt" and //span[@class = "z-label" and .= "Data Tidak Ditemukan"]]//td[@class = "z-button-cm" and .= "OK"]')
				btnOkNotFound.click()
				msg = 'Aju tidak ditemukan atau belum mendapat respon NPE/PPB'
				is_end = True
				self.updateStatus(msg, is_end)

	def chooseResponses(self, rows):
		print('Choose response..')
		chosenResponses = ['NPE', 'PPB', 'BCF']
		self.responses = []

		for row in rows:
			jnResp = html.unescape(row.find_element_by_css_selector('td:nth-child(3) > div').get_attribute('innerHTML'))
			print(jnResp)
			if any(word in jnResp for word in chosenResponses):
				self.responses.append(jnResp)
		self.responses = tuple(set(self.responses))

		if len(self.responses) > 0:
			for rs in self.responses:
				self.sendResponses(rs)
			msg = 'Selesai'
			is_end = True
			self.updateStatus(msg, is_end)
		else:
			msg = 'Aju ini belum mendapat respon NPE atau PPB'
			is_end = True
			self.updateStatus(msg, is_end)

	def sendResponses(self, response):
		print('Send response..')

		btnKrm = self.driver.find_element_by_xpath(f'//div[@class = "z-listbox"][2]//tbody[contains(@id, "rows")]/tr[contains(@class, "z-listitem") and ./td/div[.= "{response}"]]//td[@class = "z-button-cm" and .="Kirim"]')
		btnKrm.click()
		checkModalOk = EC.presence_of_element_located((By.XPATH, '//div[@class = "z-window-modal z-window-modal-shadow" and .//span[@class = "z-label" and .= "Data Berhasil Dikirim"]]'))
		WebDriverWait(self.driver, 120).until(checkModalOk)
		btnOk = self.driver.find_element_by_xpath('//div[@class = "z-window-modal z-window-modal-shadow" and .//span[@class = "z-label" and .= "Data Berhasil Dikirim"]]//td[@class = "z-button-cm" and .= "OK"]')
		btnOk.click()
		self.updateStatus(f'{response} berhasil dikirim')

	def updateRequest(self, perusahaan):
		# Update nama perusahaan ke request table
		request = Request.query.filter_by(id=self.req_id).first()
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
		print('PEB always on')
		btnDate = self.driver.find_element_by_css_selector('.z-datebox-btn')
		btnDate.click()
		time.sleep(1)
		btnDate.click()
		self.is_idle = True