import os

app_name = "REPORTS_GFSS"
public_name = "АИС ГФСС"

# 
app_home="C:/Projects"
platform='!unix'
ORACLE_HOME=r'C:\instantclient_21_3'

if "HOME" in os.environ:
    app_home=os.environ["HOME"]
    platform='unix'

if "ORACLE_HOME" in os.environ:
    ORACLE_HOME=f'{os.environ["ORACLE_HOME"]}/lib'

BASE=f'{app_home}/{app_name}'