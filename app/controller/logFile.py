import os
from datetime import datetime

def getTime():
	timeNow = datetime.now().strftime('%Y_%m_%d_%H%M%S')
	return timeNow

def rename():
	timeNow = getTime()
	fileNames = [
		['logs/access.log', f'logs/{timeNow}_access.log'],
		['logs/error.log', f'logs/{timeNow}_error.log']
	]
	for name in fileNames:
		if os.path.exists(name[0]):
			os.rename(name[0], name[1])