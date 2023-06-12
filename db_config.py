from ais_gfss_parameter import using
from util.logger import log
import redis

if using.startswith('PROD'):
    LIB_DIR = r'/home/ais_gfss/instantclient_21_8'
elif using == 'DEV_WIN_HOME':
    LIB_DIR = r'd:/install/oracle/instantclient_19_13'
else:
    LIB_DIR = r'C:\instantclient_21_3'

if using == 'PROD':
    pool_min = 20
    pool_max = 40
    pool_inc = 20
    Debug = True
else:
    pool_min = 4
    pool_max = 10
    pool_inc = 4
    Debug = True

report_db_dsn = '172.16.17.12:1521/gfss'
report_db_user = 'sswh'
report_db_password = 'sswh'
dsn = '192.168.20.60:1521/gfssdb.gfss.kz'
username = 'reports'
password = 'reports'
encoding = 'UTF-8'
timeout = 15       # В секундах. Время простоя, после которого курсор освобождается
wait_timeout = 15000  # Время (в миллисекундах) ожидания доступного сеанса в пуле, перед тем как выдать ошибку
max_lifetime_session = 30  # Время в секундах, в течении которого может существоват сеанс

log.info(f"=====> DB CONFIG. using: {using}, LIB_DIR: {LIB_DIR}, DSN: {dsn}")

# if using != 'DEV_WIN_HOME':
#     db_redis = redis.from_url('redis://@10.15.15.11:6379')
#     log.info(f"=====> REDIS CREATED. using url: redis://@10.15.15.11:6379")

class SessionConfig:
    # secret_key = 'this is secret key qer:ekjf;keriutype2tO287'
    SECRET_KEY = 'this is secret key 12345 -'
    if using.startswith('DEV'):
        #SESSION_TYPE = "filesystem"
        SESSION_TYPE = 'redis'
        SESSION_REDIS = redis.from_url('redis://@192.168.20.33:6379')
    else:
        #SESSION_TYPE = "filesystem"
        SESSION_TYPE = 'redis'
        SESSION_REDIS = redis.from_url('redis://@192.168.20.33:6379')
    SESSION_USE_SIGNER = True
    # SESSION_REDIS = Redis(host='10.15.15.11', port='6379')
    # SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3000
    # SQLALCHEMY_DATABASE_URI = f'oracle+cx_oracle://{username}:{password}@{dsn}'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    print(f"----------> TYPE SESSION: {SESSION_TYPE}")
