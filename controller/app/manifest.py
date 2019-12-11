import time
from bs4 import BeautifulSoup
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
		self.responses = []
		
	def openPage(self):
		driver = Login(self.url)
		driver = driver.login()
		return driver

	def openMenu(self):
		driver = self.openPage()

		print('Open menu..')
		menuUtility = driver.find_element_by_css_selector('.z-menu:nth-child(4) button')
		menuUtility.click()

		menuRespon = driver.find_element_by_css_selector('.z-menu-popup li:nth-child(1) a')
		menuRespon.click()

		pre.waitLoading(driver)

		return driver

	def getResponses(self, tglAwal, tglAkhir, noAju):
		driver = self.openMenu()

		try:
			checkInputTgl = EC.presence_of_element_located((By.CLASS_NAME, 'z-datebox-inp'))
			WebDriverWait(driver, 10).until(checkInputTgl)
		except TimeoutException:
			print('Timeout to load page..')
		else:
			print('Collect responses..')
			inputTgl = driver.find_elements_by_css_selector('.z-datebox-inp')
			inputTglAwal = inputTgl[0]
			inputTglAkhir = inputTgl[1]

			inputText = driver.find_elements_by_css_selector('.z-textbox')
			inputAju = inputText[1]

			btnCari = driver.find_element_by_xpath('//button[contains(., "Cari")]')

			inputTglAwal.click()
			driver.execute_script('arguments[0].value = arguments[1]', inputTglAwal, tglAwal)
			inputTglAkhir.click()
			driver.execute_script('arguments[0].value = arguments[1]', inputTglAkhir, tglAkhir)
			inputAju.send_keys(noAju)
			btnCari.click()

			time.sleep(1)
			rows = driver.find_elements_by_css_selector('.z-listbox-body tbody:nth-child(2) > tr')
			self.parseResponses(rows)

			# try:
			# 	WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_css_selector('.z-listbox-body > table > tbody:nth-child(2)').text.strip() != '')
			# except TimeoutException:
			# 	print('Data not found..')
			# else:
			# 	rows = driver.find_elements_by_css_selector('.z-listbox-body tbody:nth-child(2) > tr')
			# 	self.parseResponses(rows)

	def parseResponses(self, rows):
		print('Parse responses..')
		for row in rows:
			cols = row.find_elements_by_css_selector('td > div')
			jnResp = cols[1].get_attribute('innerHTML')
			noBc10 = cols[5].get_attribute('innerHTML')
			noBc11 = cols[6].get_attribute('innerHTML')
			tgResp = cols[8].get_attribute('innerHTML')
			btnKrm = cols[10].find_element_by_css_selector('button').get_attribute('id')
			dataResponse = [jnResp, noBc10, noBc11, tgResp, btnKrm]
			self.responses.append(dataResponse)
		print(self.responses)