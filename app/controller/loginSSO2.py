import os, requests, shortuuid, shutil, urllib.request
from pathlib import Path
from PIL import Image
from pyzbar.pyzbar import decode
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from respon import app, db

class LoginSSO2(object):
	def __init__(
			self, 
			url="http://sso.customs.go.id", 
			ceisa_app="impor",
			xpathLoginCheck=""
		):
		self.url = url
		self.ceisa_app = ceisa_app
		self.is_login = False
		self.login_id = shortuuid.uuid()
		self.imgDir = f'output/qrsso2/{self.login_id}'
		self.xpathLoginCheck = xpathLoginCheck

	def login(self):
		self.openLoginPage()
		self.getQr()
		txtQr = self.readQr()
		self.sendRequest(txtQr)
		self.is_login = self.checkLogin()

	def openLoginPage(self):
		options = Options()
		options.headless = False

		caps = DesiredCapabilities().FIREFOX
		caps["pageLoadStrategy"] = "eager"

		# create a new Firefox session
		self.driver = webdriver.Firefox(
			options=options, 
			capabilities=caps, 
			executable_path=app.config['PATH_GECKODRIVER'], 
			service_log_path=app.config['PATH_GECKODRIVER_LOG']
		)
		self.driver.get(self.url)
		xpathSignupBody = "//body[@class='signup-page']"
		checkSignupBody = EC.visibility_of_element_located((By.XPATH, xpathSignupBody))
		WebDriverWait(self.driver, 60).until(checkSignupBody)

	def getQr(self):
		xpathQrCode = "//div[@id='qrcode']/img"
		checkQrCode = EC.visibility_of_element_located((By.XPATH, xpathQrCode))
		qrCode = WebDriverWait(self.driver, 60).until(checkQrCode)
		src = qrCode.get_attribute('src')

		Path(self.imgDir).mkdir(parents=True, exist_ok=True)
		urllib.request.urlretrieve(src, f"{self.imgDir}/qr.png")

	def readQr(self):
		decoded = decode(Image.open(f'{self.imgDir}/qr.png'))
		txt = str(decoded[0].data)
		arrTxt = txt.split("/")
		txtQr = arrTxt[-1].replace("'", "")
		print("txtQr", txtQr)
		return txtQr

	def sendRequest(self, txtQr):
		url = "https://api.beacukai.go.id/cehris2/apisso2.html"
		header = {
			"token": app.config['SSO2_TOKEN'],
			"beacukai-api-key": app.config['BEACUKAI_API_KEY'],
			# "If-Modified-Since": "%a, %d %b %Y %H:%M:%S GMT%z",
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
			"User-Agent": "Linux",
			"Host": "api.beacukai.go.id",
			"Connection": "Keep-Alive",
			"Accept-Encoding": "gzip"
		}
		body = {
			# "txtDeviceId":"xxxxxxxxxxxxxxxx",
			"txtNip": app.config['USER_NIP'],
			# "txtLng": 0.0,
			# "txtDeviceOs": "samsung",
			# "txtLat": 0.0,
			"txtKdkantor": app.config['USER_KD_KANTOR'],
			"txtKeyCode": app.config['SSO2_TOKEN'],
			"content": "sign-qr",
			"txtQr": txtQr
		}
		data = urllib.parse.urlencode(body)

		x = requests.post(url, data=data, headers=header)
		print("response", x.content)

	def emptyDir(self):
		files = glob(f'{self.imgDir}/*')
		for f in files:
			os.remove(f)

	def checkLogin(self):
		try:
			checkElement = EC.presence_of_element_located((By.XPATH, self.xpathLoginCheck))
			WebDriverWait(self.driver, 60).until(checkElement)
		except TimeoutException:
			print("LOGIN FAILED")
			return False
		except Exception as e:
			raise e
		else:
			print("LOGIN SUCCESSFUL")
			shutil.rmtree(self.imgDir)
			return True