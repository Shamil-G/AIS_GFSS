from __init__ import app, log
import app_config as cfg
#from db.user_login import * 
from view.routes import *

from gfss_parameter import SSO_LOGIN
if SSO_LOGIN:
    from db.user_login_sso import *
else:
    from ldap.user_login import *


if __name__ == "__main__":
    log.info(f"===> Main REPORTS-GFSS started on {cfg.host}:{cfg.port}, work_dir: {cfg.BASE}")
    app.run(host=cfg.host, port=cfg.port, debug=False)
