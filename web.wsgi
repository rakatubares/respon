import os, sys
 
sys.path.insert(0, 'C:/laragon/www/respon/')

os.environ['FLASK_ENV'] = 'production'
 
from respon import app as application