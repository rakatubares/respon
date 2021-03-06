import os, sys
sys.path.append("..")

import getpass
import shortuuid
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from respon import app, db
from app.models import SignIn

class Login(object):
	"""docstring for Login"""
	def __init__(self, url='http://ceisa.customs.go.id', ceisa_app='sso'):
		super(Login, self).__init__()
		self.url = url
		self.ceisa_app = ceisa_app
		self.driver = ''
		self.is_login = False
		self.login_id = shortuuid.uuid()

	def login(self):

		while self.is_login == False:
			print('Try logging in...')
			try:
				self.driver.find_element_by_id('txtUserName')
			except AttributeError:
				self.openLoginPage()
			else:
				self.inputUserPassword()
		else:
			return self.driver

	def openLoginPage(self):
		print('Open login page..')

		# Create activity id in database
		act = SignIn(hash=self.login_id, status=f'{self.ceisa_app} start')
		db.session.add(act)
		db.session.commit()

		options = Options()
		options.headless = True

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
		login_form = EC.presence_of_element_located((By.ID, 'txtUserName'))
		WebDriverWait(self.driver, 120).until(login_form)

	def inputUserPassword(self):
		print('Input login details..')
		try:
			# Wait login form
			checkUserName = EC.presence_of_element_located((By.ID, 'txtUserName'))
			WebDriverWait(self.driver, 120).until(checkUserName)
		except Exception as e:
			try:
				self.driver.close()
				self.driver.quit()
			except AttributeError:
				pass
			except Exception as e:
				raise e
			finally:
				self.login()
		else:
			# Find login form
			inputUserName = self.driver.find_element_by_id("txtUserName")
			inputUserPass = self.driver.find_element_by_id("txtUserPassword")
			submitButton = self.driver.find_element_by_id("btnSubmit")

			# Input username and password
			userName = app.config['CEISA_USER']
			password = app.config['CEISA_PASSWORD']

			inputUserName.send_keys(userName)
			inputUserPass.send_keys(password)
			submitButton.click()

			# Try login
			# timeout = 30
			try:
				if self.url == 'http://ceisa.customs.go.id':
					menu = EC.presence_of_element_located((By.ID, 'divApp'))
				else:
					menu = EC.presence_of_element_located((By.CLASS_NAME, 'z-menubar-hor'))
				WebDriverWait(self.driver, 120).until(menu)
				self.is_login = True
				
				# Store logged in status in database
				act = SignIn(hash=self.login_id, status=f'{self.ceisa_app} logged in')
				db.session.add(act)
				db.session.commit()
			except TimeoutException:
				print("Timed out waiting for page to load")
			except UnexpectedAlertPresentException:
				print("Invalid password !")