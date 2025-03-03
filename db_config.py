from gfss_parameter import platform, ORACLE_HOME
from util.logger import log
from redis import from_url
# import redis

if platform == 'unix':
    pool_min = 1
    pool_max = 40
    pool_inc = 10
    username = 'reports'
else:
    pool_min = 4
    pool_max = 10
    pool_inc = 4
    username = 'reports_test'

report_db_dsn = '172.31.33.29:1521/gfss'
report_db_user = 'sswh'
report_db_password = 'sswh'
dsn = '192.168.20.60:1521/gfssdb.gfss.kz'
password = 'reports'

expire_time = 2  # количество минут между отправкой keepalive
tcp_connect_timeout = 5 # Кол-во секунд ождания установления соединения
timeout = 300     # В секундах. Время простоя, после которого курсор освобождается
wait_timeout = 2000  # Время (в миллисекундах) ожидания доступного сеанса в пуле, перед тем как выдать ошибку
max_lifetime_session = 180  # Время в секундах, в течении которого может существоват сеанс
retry_count = 1
retry_delay = 2

Debug = True

log.info(f"=====> DB CONFIG. platform: {platform}, ORACLE_HOME: {ORACLE_HOME}, DSN: {dsn}")

# if using != 'DEV_WIN_HOME':
#     db_redis = redis.from_url('redis://@10.15.15.11:6379')
#     log.info(f"=====> REDIS CREATED. using url: redis://@10.15.15.11:6379")

class SessionConfig:
    # secret_key = 'this is secret key qer:ekjf;keriutype2tO287'
    SECRET_KEY = 'this is secret key 12345 -'
    if platform!='unix':
        #SESSION_TYPE = "filesystem"
        SESSION_TYPE = 'redis'
        SESSION_REDIS = from_url('redis://@192.168.20.33:6379')
    else:
        #SESSION_TYPE = "filesystem"
        SESSION_TYPE = 'redis'
        SESSION_REDIS = from_url('redis://@192.168.20.33:6379')
    SESSION_USE_SIGNER = True
    # SESSION_REDIS = Redis(host='10.15.15.11', port='6379')
    # SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3000
    # SQLALCHEMY_DATABASE_URI = f'oracle+cx_oracle://{username}:{password}@{dsn}'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    print(f"----------> TYPE SESSION: {SESSION_TYPE}")
