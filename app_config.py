from reports_gfss_parameter import BASE

styles = 'styles'

debug=False

host = 'localhost'
port=5090
src_lang = 'file'
language = 'ru'
URL_LOGIN = 'http://192.168.1.34:8000'
LOG_PATH = f"{BASE}/logs"
REPORT_MODULE_PATH = f"reports"
REPORT_PATH = f"{BASE}/spool"
UPLOAD_PATH = f"{BASE}/uploads"

ldap_admins = ['Гусейнов Шамиль Аладдинович', 'Алибаева Мадина Жасулановна', 'Маликов Айдар Амангельдыевич']
ldap_server = 'ldap://192.168.1.3:3268'
ldap_user = 'cn=ldp,ou=admins,dc=gfss,dc=kz'
ldap_password = 'hu89_fart7'
ldap_ignore_ou = ['UVOLEN',]
ldap_boss = ['Директор', 'Руководитель','Главный разработчик']
