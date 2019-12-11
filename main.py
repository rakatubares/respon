from bs4 import BeautifulSoup

from controller.app.manifest import Manifest

manif = Manifest()
driver = manif.getResponses('051219', '151219', '18052829061820191207000012')
# html = driver.page_source
# soup = BeautifulSoup(html)
# print(soup.prettify())