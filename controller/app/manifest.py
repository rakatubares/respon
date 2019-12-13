import time
from bs4 import BeautifulSoup
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from controller import preprocess as pre
from controller.login import Login

class Manifest(object):
	"""docstring for Manifest"""
	def __init__(self):
		super(Manifest, self).__init__()
		self.url = 'http://manif-in.customs.go.id/beacukai-manifes'
		self.driver = ''
		self.responses = []
		
	def openPage(self):
		self.driver = Login(self.url)
		self.driver = self.driver.login()
		return self.driver

	def openMenu(self):
		self.driver = self.openPage()

		print('Open menu..')
		menuUtility = self.driver.find_element_by_css_selector('.z-menu:nth-child(4) button')
		menuUtility.click()

		menuRespon = self.driver.find_element_by_css_selector('.z-menu-popup li:nth-child(1) a')
		menuRespon.click()

		pre.waitLoading(self.driver)

	def getResponses(self, tglAwal, tglAkhir, noAju):
		try:
			checkInputTgl = EC.presence_of_element_located((By.CLASS_NAME, 'z-datebox-inp'))
			WebDriverWait(self.driver, 10).until(checkInputTgl)
		except TimeoutException:
			print('Timeout to load page..')
		else:
			print('Collect responses..')
			inputTgl = self.driver.find_elements_by_css_selector('.z-datebox-inp')
			inputTglAwal = inputTgl[0]
			inputTglAkhir = inputTgl[1]

			inputText = self.driver.find_elements_by_css_selector('.z-textbox')
			inputAju = inputText[1]

			btnCari = self.driver.find_element_by_xpath('//button[contains(., "Cari")]')

			# Handling input tgl awal
			inputTglAwal.clear()
			inputTglAwal.click()
			self.driver.execute_script('arguments[0].value = arguments[1]', inputTglAwal, tglAwal)
			# Handling input tgl akhir
			inputTglAkhir.clear()
			inputTglAkhir.click()
			self.driver.execute_script('arguments[0].value = arguments[1]', inputTglAkhir, tglAkhir)
			# Handling input aju
			inputAju.clear()
			inputAju.send_keys(noAju)
			btnCari.click()

			time.sleep(1)
			rows = self.driver.find_elements_by_css_selector('.z-listbox-body tbody:nth-child(2) > tr')
			self.parseResponses(rows)
			self.sortResponses()

			return self.responses

	def parseResponses(self, rows):
		print('Parse responses..')
		self.responses = []
		for row in rows:
			cols = row.find_elements_by_css_selector('td > div')
			jnResp = cols[1].get_attribute('innerHTML')
			noBc10 = cols[5].get_attribute('innerHTML')
			noBc11 = cols[6].get_attribute('innerHTML')
			tgResp = cols[8].get_attribute('innerHTML')
			btnKrm = cols[10].find_element_by_css_selector('button').get_attribute('id')
			dataResponse = [jnResp, noBc10, noBc11, tgResp, btnKrm]
			self.responses.append(dataResponse)
	
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
		else:
			confirmBtn = self.driver.find_element_by_xpath('//button[contains(@class, "z-messagebox-btn") and contains(., "Yes")]')
			confirmBtn.click()
			return [1,'Respon telah dikirim']