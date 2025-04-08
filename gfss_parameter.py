from os import environ

debug = True
app_name = "REPORTS_GFSS"
public_name = "Большие отчеты в АО ГФСС"
SSO_LOGIN = True
http_ip_context='HTTP_X_FORWARDED_FOR'
#http_ip_context='HTTP_X_REAL_IP'

# 
app_home="C:/Projects"
platform='!unix'
ORACLE_HOME=r'C:\instantclient_21_3'
LD_LIBRARY_PATH=f'{ORACLE_HOME}'

if "HOME" in environ:
    app_home=environ["HOME"]
    platform='unix'

if "ORACLE_HOME" in environ:
    ORACLE_HOME=f'{environ["ORACLE_HOME"]}'
    LD_LIBRARY_PATH=f'{ORACLE_HOME}/lib'

BASE=f'{app_home}/{app_name}'