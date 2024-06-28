import multiprocessing
from reports_gfss_parameter import app_name, BASE
from app_config import port

bind = f"localhost:{port}"
workers = int(multiprocessing.cpu_count()*2) + 1
worker_class = "gevent"
print(f'GUNICORN. change DIRECTORY: {BASE}')

chdir = BASE

wsgi_app = "wsgi:app"
loglevel = 'info'
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s"  "%(a)s"'
accesslog = "logs/reports-gunicorn-access.log"

error_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s"  "%(a)s"'
errorlog = "logs/reports-gunicorn-error.log"
proc_name = f'{app_name}'
# Перезапуск после N кол-во запросов
max_requests = 0
# Перезапуск, если ответа не было более 60 сек
timeout = 180
# umask or -m 007
umask = 0x007
# Проверка IP адресов, с которых разрешено обрабатывать набор безопасных заголовков
forwarded_allow_ips = '192.169.1.33,127.0.0.1'
#preload увеличивает производительность - хуже uwsgi!
preload_app = 'True'