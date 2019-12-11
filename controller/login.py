import sys
sys.path.append("..")

import getpass
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import apps.config as cfg

class Login(object):
	"""docstring for Login"""
	def __init__(self, url='http://ceisa.customs.go.id'):
		super(Login, self).__init__()
		self.url = url
		self.driver = ''
		self.is_login = False

	def login(self):

		while self.is_login == False:
			print('Try logging in...')
			try:
				self.driver.find_element_by_id('txtUserName')
			except AttributeError:
				self.openLoginPage()
			finally:
				self.inputUserPassword()
		else:
			return self.driver

	def openLoginPage(self):
		print('Open login page..')
		options = Options()
		# options.add_argument('--headless')

		# create a new Firefox session
		self.driver = webdriver.Firefox(options=options)
		self.driver.get(self.url)
		login_form = EC.presence_of_element_located((By.ID, 'txtUserName'))
		WebDriverWait(self.driver, 30).until(login_form)

	def inputUserPassword(self):
		print('Input login details..')
		# Find login form
		inputUserName = self.driver.find_element_by_id("txtUserName")
		inputUserPass = self.driver.find_element_by_id("txtUserPassword")
		submitButton = self.driver.find_element_by_id("btnSubmit")

		# Input username and password
		userName = cfg.user['username']
		password = cfg.user['password']

		inputUserName.send_keys(userName)
		inputUserPass.send_keys(password)
		submitButton.click()

		# Try login
		timeout = 30
		try:
			if self.url == 'http://ceisa.customs.go.id':
				menu = EC.presence_of_element_located((By.ID, 'divApp'))
			else:
				menu = EC.presence_of_element_located((By.CLASS_NAME, 'z-menubar-hor'))
			WebDriverWait(self.driver, timeout).until(menu)
			self.is_login = True
		except TimeoutException:
			print("Timed out waiting for page to load")
		except UnexpectedAlertPresentException:
			print("Invalid password !")