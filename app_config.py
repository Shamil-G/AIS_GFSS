from reports_gfss_parameter import platform, BASE

if platform=='unix':
    debug_level = 2
    host = 'localhost'
else:
    host = '192.168.5.17'
    debug_level = 2

port=5090
src_lang = 'file'
language = 'ru'
debug = True
#URL_LOGIN = 'http://192.168.1.35:8010'
URL_LOGIN = 'http://192.168.1.33:8000'
LOG_PATH = f"{BASE}/logs"
REPORT_MODULE_PATH = f"reports"
REPORT_PATH = f"{BASE}/spool"