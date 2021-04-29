import html, threading, time
from datetime import datetime
from flask_socketio import emit
from pprint import pprint
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from respon import app, db, socketio
from app.controller import preprocess as pre
from app.controller.loginSSO2 import LoginSSO2
from app.models import SignIn, Request, Status

class Impor(object):
	def __init__(self):
		self.url = "http://impor.customs.go.id/beacukai-impor/"
		self.ceisa_app = "impor"
		self.xpathLoginCheck = "//iframe[@src='http://sso.customs.go.id/SSO2/HeaderApps?nextUrl=http://impor.customs.go.id/beacukai-impor&appCode=36']"
		self.is_alive = True
		self.is_idle = True
		self.initiateBot()

	### BOT INITIATION ###
	def initiateBot(self):
		self.is_idle = False
		self.openPage()
		self.openMenu()
		self.alwaysOn()
		self.is_idle = True

	def openPage(self):
		log = LoginSSO2(self.url, self.ceisa_app, self.xpathLoginCheck)
		log.login()
		self.driver = log.driver
		self.hash = log.login_id

	def openMenu(self):
		# Klik menu browse
		xpathMenuBrowse = "//td[@class='z-menu'][.//button[@class='z-menu-btn'][text()='Browse\u00a0']]"
		checkMenuBrowse = EC.element_to_be_clickable((By.XPATH, xpathMenuBrowse))
		menuBrowse = WebDriverWait(self.driver, 30).until(checkMenuBrowse)
		menuBrowse.click()
		pre.waitLoading(self.driver)

		# Klik menu kirim ulang
		xpathMenuKirimUlang = "//div[@class='z-menu-popup z-menu-popup-shadow']//li[@class='z-menu-item'][.//a[@class='z-menu-item-cnt'][text()=' Browse Cetak Kirim Ulang Semua Respon']]"
		checkMenuKirimUlang = EC.element_to_be_clickable((By.XPATH, xpathMenuKirimUlang))
		menuKirimUlang = WebDriverWait(self.driver, 30).until(checkMenuKirimUlang)
		menuKirimUlang.click()
		pre.waitLoading(self.driver)

		# Check page
		xpathHeader = "//div[@class='z-window-embedded-header'][text()='BROWSE DAN CETAK SEMUA RESPON']"
		checkHeader = EC.presence_of_element_located((By.XPATH, xpathHeader))
		WebDriverWait(self.driver, 30).until(checkHeader)

		# Pilih filter car
		xpathFilterType = "(//input[@class='z-combobox-inp z-combobox-readonly'])[1]"
		checkFilterType = EC.element_to_be_clickable((By.XPATH, xpathFilterType))
		dropdownFilterType = WebDriverWait(self.driver, 5).until(checkFilterType)
		dropdownFilterType.click()

		xpathItemFilterType = "//div[@class='z-combobox-pp z-combobox-shadow']//tr[@class='z-comboitem'][.//td[@class='z-comboitem-text'][text()='Car\u00a0\u00a0\u00a0\u00a0:']]"
		checkItemFilterType = EC.element_to_be_clickable((By.XPATH, xpathItemFilterType))
		itemFilterType = WebDriverWait(self.driver, 5).until(checkItemFilterType)
		self.driver.execute_script('arguments[0].click()', itemFilterType)
		pre.waitLoading(self.driver)

		xpathInputAju = "//input[contains(@class, 'z-textbox')][@maxlength='26']"
		checkInputAju = EC.presence_of_element_located((By.XPATH, xpathInputAju))
		WebDriverWait(self.driver, 30).until(checkInputAju)

	def alwaysOn(self):
		threading.Timer(300, self.alwaysOn).start()
		if self.is_idle == True:
			self.is_idle = False
			try:
				print(f'{self.ceisa_app} always on')
				tabPib = self.driver.find_element_by_xpath('//span[@class = "z-tab-text" and .= "PIB"]')
				tabPib.click()
				checkInputTgl = EC.presence_of_element_located((By.CLASS_NAME, 'z-datebox-inp'))
				WebDriverWait(self.driver, 10).until(checkInputTgl)
				btnDate = self.driver.find_element_by_css_selector('.z-datebox-btn')
				btnDate.click()
				time.sleep(1)
				btnDate.click()
			except Exception:
				applog = SignIn(hash=self.hash, status=f'{self.ceisa_app} restart')
				db.session.add(applog)
				db.session.commit()
				self.closeDriver()
				self.initiateBot()
			self.is_idle = True

	def closeDriver(self):
		self.driver.close()
		self.driver.quit()

	### SENDING RESPONSE ###
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
			print(f'PIB [ID:{self.req_id}] - Timeout to load page..')

			# Store error in status table
			msg = 'Gagal membuka halaman pencarian. Coba beberapa saat lagi.'
			is_end = True
			self.updateStatus(msg, is_end)
		except Exception as e:
			raise e
		else:
			print(f'PIB [ID:{self.req_id}] - Collect responses..')

			# Update status table
			msg = 'Mencari respon'
			self.updateStatus(msg)
			self.findPib(tglAwal, tglAkhir, noAju)

		self.is_idle = True

	def findPib(self, tglAwal, tglAkhir, noAju):
		print(f'PIB [ID:{self.req_id}] - finding PIB..')
		tab = 'PIB'
		tabPib = self.driver.find_element_by_xpath('//span[@class = "z-tab-text" and .= "PIB"]')
		tabPib.click()
		pre.waitLoading(self.driver)
		checkHeaderPib = EC.visibility_of_element_located((By.XPATH, "//div[@class='z-window-embedded-header'][text()='PIB']"))
		WebDriverWait(self.driver, 5).until(checkHeaderPib)

		self.inputAju(noAju, tab)
		self.inputTanggal(tglAwal, tglAkhir, tab)
		self.tampilkanData(tab)
		pibFound = self.checkAju(noAju, tab)
		if pibFound:
			self.chooseResponses(tab)
			self.kosongkanData(tab)
		else:
			self.findProses(tglAwal, tglAkhir, noAju)

	def findProses(self, tglAwal, tglAkhir, noAju):
		print(f'PIB [ID:{self.req_id}] - finding PIB tab PROSES..')
		tab = 'PROSES'
		tabProses = self.driver.find_element_by_xpath('//span[@class = "z-tab-text" and .= "PROSES"]')
		tabProses.click()
		pre.waitLoading(self.driver)
		checkHeaderProses = EC.visibility_of_element_located((By.XPATH, "//div[@class='z-window-embedded-header'][text()='Proses']"))
		WebDriverWait(self.driver, 5).until(checkHeaderProses)

		self.inputAju(noAju, tab)
		self.inputTanggal(tglAwal, tglAkhir, tab)
		self.tampilkanData(tab)
		pibFound = self.checkAju(noAju, tab)
		if pibFound:
			self.chooseResponses(tab)
			self.kosongkanData(tab)
		else:
			msg = 'Aju tidak ditemukan'
			is_end = True
			self.updateStatus(msg, is_end)

	def inputAju(self, noAju, tab):
		tabNum = {
			'PIB': '1',
			'PROSES': '3'
		}
		xpathInputAju = f'//div[@class = "z-tabpanels"]/div[{tabNum[tab]}]//input[@class = "z-textbox" and @maxlength="26"]'
		checkInputAju = EC.presence_of_element_located((By.XPATH, xpathInputAju))
		inputAju = WebDriverWait(self.driver, 5).until(checkInputAju)
		self.driver.execute_script('arguments[0].value = arguments[1]', inputAju, noAju)
		inputAju.click()

	def inputTanggal(self, filterTglAwal, filterTglAkhir, tab):
		tabNum = {
			'PIB': '1',
			'PROSES': '3'
		}

		# Check value tgl awal
		xpathInputTglAwal = f"//div[@class='z-tabpanels']/div[{tabNum[tab]}]//td[1]/i/input[@class='z-datebox-inp']"
		checkInputTglAwal = EC.element_to_be_clickable((By.XPATH, xpathInputTglAwal))
		inputTglAwal = WebDriverWait(self.driver, 5).until(checkInputTglAwal)
		tglAwalVal = inputTglAwal.get_attribute('value')
		tglAwal = datetime.strptime(tglAwalVal, '%d-%m-%Y')

		# Input tgl awal
		filterTglAwalDate = datetime.strptime(filterTglAwal, '%d%m%y')
		if filterTglAwalDate != tglAwal:
			inputTglAwal.clear()
			inputTglAwal.click()
			self.driver.execute_script('arguments[0].value = arguments[1]', inputTglAwal, filterTglAwal)
			xpathInputReadOnly = f"//div[@class='z-tabpanels']/div[{tabNum[tab]}]//input[@class='z-textbox z-textbox-real-readonly z-textbox-readonly']"
			inputTxt = self.driver.find_element_by_xpath(xpathInputReadOnly)
			inputTxt.click()

		# Check value tgl akhir
		checkInputTglAkhir = EC.element_to_be_clickable((By.XPATH, f"//div[@class='z-tabpanels']/div[{tabNum[tab]}]//td[5]/i/input[@class='z-datebox-inp']"))
		inputTglAkhir = WebDriverWait(self.driver, 5).until(checkInputTglAkhir)
		tglAkhirVal = inputTglAkhir.get_attribute('value')
		tglAkhir = datetime.strptime(tglAkhirVal, '%d-%m-%Y')

		# Input tgl akhir
		filterTglAkhirDate = datetime.strptime(filterTglAkhir, '%d%m%y')
		if filterTglAkhirDate != tglAkhir:
			inputTglAkhir.clear()
			inputTglAkhir.click()
			self.driver.execute_script('arguments[0].value = arguments[1]', inputTglAkhir, filterTglAkhir)
			xpathInputReadOnly = f"//div[@class='z-tabpanels']/div[{tabNum[tab]}]//input[@class='z-textbox z-textbox-real-readonly z-textbox-readonly']"
			inputTxt = self.driver.find_element_by_xpath(xpathInputReadOnly)
			inputTxt.click()

	def tampilkanData(self, tab):
		tabNum = {
			'PIB': '1',
			'PROSES': '3'
		}

		btnTampilkan = self.driver.find_element_by_xpath(f'//div[@class = "z-tabpanels"]/div[{tabNum[tab]}]//td[@class = "z-button-cm" and .= "Tampilkan"]')
		btnTampilkan.click()
		time.sleep(1)
		pre.waitLoading(self.driver, 120)

	def checkAju(self, noAju, tab):
		colNum = {
			'PIB': '5',
			'PROSES': '3'
		}

		try:
			errorBox = ''
			errorBox = self.driver.find_element_by_xpath('//div[contains(@class, "z-messagebox")]/span[contains(@class, "z-label") and contains(., "Unknown exception")]')
			while 'errorBox' != '':
				self.getResponses(tglAwal, noAju)
		except NoSuchElementException:
			try:
				boxNotFound = self.driver.find_element_by_xpath('//div[@class = "z-window-modal-cnt" and //span[@class = "z-label" and .= "Data Tidak Ditemukan"]]')
			except NoSuchElementException:
				txtAju = noAju[:6] + '-' + noAju[6:12] + '-' + noAju[12:20] + '-' + noAju[20:]
				xpathRowAju = f"//div[@class='z-listbox-body']//tr[contains(@class,'z-listitem')][.//td[{colNum[tab]}]/div[@class='z-listcell-cnt z-overflow-hidden'][text()='{txtAju}']]"
				checkRowAju = EC.element_to_be_clickable((By.XPATH, xpathRowAju))
				rowAju = WebDriverWait(self.driver, 5).until(checkRowAju)
				colsHeader = rowAju.find_elements_by_css_selector('td > div')

				if tab == 'PIB':
					tglPib = colsHeader[0].get_attribute('innerHTML')
					noPib = colsHeader[1].get_attribute('innerHTML')
					self.updateStatus(f'PIB no {noPib} tgl {tglPib} ditemukan')

					importir = colsHeader[2].get_attribute('innerHTML')
					ppjk = colsHeader[3].get_attribute('innerHTML')
				elif tab == 'PROSES':
					self.updateStatus(f'PIB aju {noAju} ditemukan')

					importir = colsHeader[0].get_attribute('innerHTML')
					ppjk = colsHeader[1].get_attribute('innerHTML')

				perusahaan = ppjk if ppjk != '-' else importir
				self.updateRequest(perusahaan)

				self.driver.execute_script('arguments[0].click()', rowAju)
				time.sleep(.5)
				pre.waitLoading(self.driver)

				return True
			else:
				btnOkNotFound = self.driver.find_element_by_xpath('//div[@class = "z-window-modal-cnt" and //span[@class = "z-label" and .= "Data Tidak Ditemukan"]]//td[@class = "z-button-cm" and .= "OK"]')
				btnOkNotFound.click()
				pre.waitLoading(self.driver)
				return False

	def chooseResponses(self, tab):
		print(f'PIB [ID:{self.req_id}] - Choose response..')
		tabConstants = {
			'PIB': {
				'tabNum': '1',
				'responses': [
					"Respon SPPB", 
					"Respon SPJK",
					"Respon SPJM", 
					"Respon Ijin Pemeriksaan Lokasi(SPPF)",
					"Respon Pemberitahuan Penerimaan PIB Penyelesaian(P4)",
					"Respon Permintaan INP",
					"Respon Nota Permintaan Data dan Dokumen(NPD)",
					"Respon Surat Penetapan Barang Larangan/Pembatasan(SPBL)",
					"Respon SPKPBM(SPTNP)"
				]
			},
			'PROSES': {
				'tabNum': '3',
				'responses': [
					'Respon Billing'
				]
			}
		}

		responses = []

		rows = self.driver.find_elements_by_xpath(f'//div[@class = "z-tabpanels"]/div[{tabConstants[tab]["tabNum"]}]//div[@class = "z-listbox"][2]//tbody[contains(@id, "rows")]/tr')
		for row in rows:
			response = html.unescape(row.find_element_by_css_selector('td:nth-child(3) > div').get_attribute('innerHTML'))
			responseTime = html.unescape(row.find_element_by_css_selector('td:nth-child(2) > div').get_attribute('innerHTML'))
			responseTime = datetime.strptime(responseTime, '%d-%m-%Y %H:%M:%S')
			if response in tabConstants[tab]['responses']:
				responses.append({'time': responseTime, 'status': response})

		responses = sorted(responses, key=lambda k: k['time']) 

		if len(responses) > 0:
			for response in responses:
				if self.is_alive == True:
					print(response['status'])
					self.sendResponses(response['status'], tab)

			if self.is_alive == True:
				self.updateStatus('Selesai', True)
		else:
			if tab == 'PIB':
				self.updateStatus('Aju belum mendapat no pendaftaran', True)
			elif tab == 'PROSES':
				self.updateStatus('Aju belum mendapat no pendaftaran / billing', True)

	def sendResponses(self, response, tab):
		print(f'PIB [ID:{self.req_id}] - Send response {response}..')
		tabNum = {
			'PIB': '1',
			'PROSES': '3'
		}

		try:
			xpathBtnKirim = f"//div[@class = 'z-tabpanels']/div[{tabNum[tab]}]//div[@class = 'z-listbox'][2]//tbody[contains(@id, 'rows')]/tr[.//td[3]/div[text()='{response}']]//td[@class='z-button-cm'][text()='Kirim']"
			checkBtnKrm = EC.element_to_be_clickable((By.XPATH, xpathBtnKirim))
			btnKrm = WebDriverWait(self.driver, 30).until(checkBtnKrm)
		except TimeoutException as e:
			print(f'PIB [ID:{self.req_id}] - GAGAL MENDAPATKAN TOMBOL KIRIM {e}')
			self.updateStatus(f'Gagal kirim respon. Coba beberapa saat lagi.', True)
		except Exception as e:
			print(f'PIB [ID:{self.req_id}] - ERROR {e}')
			self.updateStatus(f'Gagal kirim respon. Coba beberapa saat lagi.', True)
			self.is_alive = False
		else:
			btnKrm.click()
			try:
				xpathBtnOk = "//div[@class='z-window-modal z-window-modal-shadow'][.//span[text()='Kirim Ulang Berhasil Dilakukan']]//td[@class='z-button-cm'][text()='OK']"
				checkBtnOk = EC.element_to_be_clickable((By.XPATH, xpathBtnOk))
				btnOk = WebDriverWait(self.driver, 30).until(checkBtnOk)
			except TimeoutException as e:
				print(f'PIB [ID:{self.req_id}] - GAGAL MENDAPATKAN TOMBOL KONFIRMASI {e}')
				self.updateStatus(f'Gagal kirim respon. Coba beberapa saat lagi.', True)
			except Exception as e:
				print(f'PIB [ID:{self.req_id}] - ERROR {e}')
				self.updateStatus(f'Gagal kirim respon. Coba beberapa saat lagi.', True)
				self.is_alive = False
			else:
				btnOk.click()
				pre.waitLoading(self.driver)
				pre.waitModalClose(self.driver)
				self.updateStatus(f'{response} berhasil dikirim')

	def kosongkanData(self, tab):
		tabNum = {
			'PIB': '1',
			'PROSES': '3'
		}

		btnKosongkan = self.driver.find_element_by_xpath(f'//div[@class = "z-tabpanels"]/div[{tabNum[tab]}]//td[@class = "z-button-cm" and .= "Kosongkan"]')
		btnKosongkan.click()
		time.sleep(1)
		pre.waitLoading(self.driver, 120)

	### STATUS HANDLING ###
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