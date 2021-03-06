from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def waitLoading(driver, timeout=10):
	try:
		loading = EC.presence_of_element_located((By.CLASS_NAME, "z-loading-indicator"))
		WebDriverWait(driver, 1).until(loading)
	except TimeoutException:
		pass
	else:
		try:
			closeLoading = EC.invisibility_of_element_located((By.CLASS_NAME, 'z-loading-indicator'))
			WebDriverWait(driver, timeout).until(closeLoading)
		except TimeoutException:
			print('Loading too long..')

def waitModalClose(driver, timeout=30):
	xpathModalMask = "//div[@class='z-modal-mask']"
	checkModalClose = EC.invisibility_of_element_located((By.XPATH, xpathModalMask))
	WebDriverWait(driver, timeout).until(checkModalClose)