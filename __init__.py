from ais_gfss_parameter import app_name

from flask import Flask
from util.logger import log


app = Flask(__name__)

app.secret_key = 'IAS GFSS Delivery secret key: 232lk;lf09ut;ih;gs'
#app.add_url_rule('/login', 'login', ldap.login, methods=['GET', 'POST'])

log.info(f"__INIT MAIN APP for {app_name} started")
print("__INIT MAIN APP__ started")

