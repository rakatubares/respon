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

class Manifest(object):
	"""docstring for Manifest"""
	def __init__(self):
		super(Manifest, self).__init__()
		self.url = 'http://manif-in.customs.go.id/beacukai-manifes'
		self.ceisa_app = 'manifest'
		self.is_idle = True
		self.searches = []
		self.req_id = 0
		self.driver = ''
		self.responses = []
		self.ur_respon = {
			11: 'RKSP',
			21: 'Manifest Inward',
			31: 'Manifest Outward'
		}
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

			inputTglAwal = self.driver.find_element_by_css_selector('.z-datebox-inp')
			inputText = self.driver.find_elements_by_css_selector('.z-textbox')
			inputAju = inputText[1]

			btnCari = self.driver.find_element_by_xpath('//button[contains(., "Cari")]')

			# Handling input tgl awal
			inputTglAwal.clear()
			inputTglAwal.click()
			self.driver.execute_script('arguments[0].value = arguments[1]', inputTglAwal, tglAwal)

			# Handling input aju
			inputAju.clear()
			inputAju.send_keys(noAju)
			btnCari.click()

			time.sleep(1)
			try:
				errorBox = ''
				errorBox = self.driver.find_element_by_xpath('//div[contains(@class, "z-messagebox")]/span[contains(@class, "z-label") and contains(., "Unknown exception")]')
				while 'errorBox' != '':
					self.getResponses(tglAwal, tglAkhir, noAju)
			except NoSuchElementException:
				print('catch element')
				rows = self.driver.find_elements_by_css_selector('.z-listbox-body tbody:nth-child(2) > tr')
				self.parseResponses(rows)
				self.updateRequest()
				self.chooseResponses()

		self.is_idle = True

	def parseResponses(self, rows):
		print('Parse responses..')
		self.responses = []
		for row in rows:
			cols = row.find_elements_by_css_selector('td > div')
			jnResp = int(cols[1].get_attribute('innerHTML'))
			pershn = cols[4].get_attribute('innerHTML')
			noBc10 = cols[5].get_attribute('innerHTML')
			noBc11 = cols[6].get_attribute('innerHTML')
			btnKrm = cols[10].find_element_by_css_selector('button').get_attribute('id')
			dataResponse = [jnResp, pershn, noBc10, noBc11, btnKrm]
			self.responses.append(dataResponse)

	def updateRequest(self):
		# Update nama perusahaan ke request table
		request = Request.query.filter_by(id=self.req_id).first()
		perusahaan = self.responses[0][1]
		request.perusahaan = perusahaan
		db.session.commit()
	
	def sortResponses(self):
		self.responses.sort(key = lambda x: datetime.strptime(x[3], '%d-%m-%Y %H:%M').strftime('%Y%m%d%H%M'), reverse = True)

	def sendResponse(self, idButton):
		idBtn = '#' + idButton
		sendBtn = self.driver.find_element_by_css_selector(idBtn)
		sendBtn.click()
		try:
			checkConfirmBtn = EC.presence_of_element_located((By.XPATH, '//button[contains(@class, "z-messagebox-btn") and contains(., "Yes")]'))
			WebDriverWait(self.driver, 10).until(checkConfirmBtn)
		except TimeoutException:
			return [0,'Gagal mengirin respon']
		except Exception as e:
			raise e
		else:
			confirmBtn = self.driver.find_element_by_xpath('//button[contains(@class, "z-messagebox-btn") and contains(., "Yes")]')
			confirmBtn.click()
			return [1,'Respon telah dikirim']

	def chooseResponses(self):
		print('Choose response..')
		print(self.responses)

		responsesToSend = []
		for r in self.responses:
			if r[0] in [11, 21, 31]:
				responsesToSend.append(r[0])
		responsesToSend = tuple(set(responsesToSend))

		if len(responsesToSend) > 0:
			for rs in responsesToSend:
				self.sendResponse2(rs)
			msg = 'Selesai'
			is_end = True
			self.updateStatus(msg, is_end)
		else:
			msg = 'Aju ini belum mendapat respon RKSP atau Manifest'
			is_end = True
			self.updateStatus(msg, is_end)

	def sendResponse2(self, kdRespon):
		print(f'Send response {kdRespon}..')
		rows = self.driver.find_elements_by_css_selector('.z-listbox-body tbody:nth-child(2) > tr')
		self.parseResponses(rows)

		clickResponses = [res for res in self.responses if res[0] == kdRespon]
		print(clickResponses)
		r = clickResponses[0]
		
		idBtn = '#' + r[4]
		sendBtn = self.driver.find_element_by_css_selector(idBtn)
		sendBtn.click()
		try:
			checkConfirmBtn = EC.presence_of_element_located((By.XPATH, '//button[contains(@class, "z-messagebox-btn") and contains(., "Yes")]'))
			WebDriverWait(self.driver, 120).until(checkConfirmBtn)
		except TimeoutException:
			# Update status table
			msg = f'Gagal mengirim respon {self.ur_respon[r[0]]}'
			self.updateStatus(msg)
		except Exception as e:
			raise e
		else:
			confirmBtn = self.driver.find_element_by_xpath('//button[contains(@class, "z-messagebox-btn") and contains(., "Yes")]')
			confirmBtn.click()
			closeMaskConfirmModal = EC.invisibility_of_element_located((By.CSS_SELECTOR, '.z-modal-mask'))
			WebDriverWait(self.driver, 120).until(closeMaskConfirmModal)
			
			# Update status table
			msg = f'Respon {self.ur_respon[r[0]]} no {r[2]} telah dikirim'
			self.updateStatus(msg)

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
