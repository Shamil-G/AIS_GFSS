from ais_gfss_parameter import using, app_name

if using.startswith('DEV_WIN'):
    BASE = f'C:/Projects/{app_name}'
else:
    BASE = f'/home/ais_gfss/{app_name}'

if using.startswith('DEV_WIN'):
    platform = '!unix'
    host = '192.168.5.17'
    debug_level = 2
    port = 8080
else:
    platform = 'unix'
    debug_level = 1
    host = 'localhost'
    port = 80

src_lang = 'file'
language = 'ru'
debug = True
URL_LOGIN = 'http://192.168.1.35:8010'
LOG_PATH = f"{BASE}/logs"
REPORT_MODULE_PATH = f"reports"
REPORT_PATH = f"{BASE}/spool"